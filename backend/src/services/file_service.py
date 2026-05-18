import uuid
import logging
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from botocore.client import Config
from fastapi import UploadFile, HTTPException, status

from src.config import settings

logger = logging.getLogger(__name__)


class FileService:
    """
    Сервис для работы с файловым хранилищем.
    Поддерживает:
    - Локальное хранилище (для разработки)
    - S3-совместимое хранилище (MinIO, AWS S3, etc.)
    """

    def __init__(self):
        """Инициализация сервиса"""
        self.use_local = settings.USE_LOCAL_STORAGE
        self.local_path = Path(settings.LOCAL_STORAGE_PATH)

        if self.use_local:
            self.local_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Local storage initialized: {self.local_path}")
        else:
            if not settings.s3_configured:
                raise RuntimeError(
                    "S3/MinIO не настроен. Проверьте переменные окружения: "
                    "S3_ENDPOINT_URL, S3_ACCESS_KEY, S3_SECRET_KEY"
                )

            boto_config = Config(
                signature_version="s3v4",
                s3={"addressing_style": "path"},
                region_name=settings.S3_REGION,
            )

            self.s3_client = boto3.client(
                "s3",
                endpoint_url=settings.S3_ENDPOINT_URL,
                aws_access_key_id=settings.S3_ACCESS_KEY,
                aws_secret_access_key=settings.S3_SECRET_KEY,
                region_name=settings.S3_REGION,
                config=boto_config,
            )
            self.bucket_name = settings.S3_BUCKET_NAME
            self.public_bucket = settings.S3_PUBLIC_BUCKET
            self.url_expiry = settings.S3_URL_EXPIRY_SECONDS

            logger.info(
                f"S3 client initialized: endpoint={settings.S3_ENDPOINT_URL}, "
                f"bucket={self.bucket_name}, public={self.public_bucket}"
            )

    async def upload_file(
        self,
        file: UploadFile,
        entity_type: str,
        entity_id: int,
        category: str,
        uploaded_by: str,
    ) -> Dict[str, Any]:
        """
        Загрузка файла в хранилище.

        Args:
            file: Загружаемый файл из FastAPI UploadFile
            entity_type: Тип сущности ('poll', 'user', etc.)
            entity_id: ID сущности
            category: Категория файла ('banner', 'avatar', etc.)
            uploaded_by: ID пользователя, загрузившего файл

        Returns:
            Dict с информацией о загруженном файле
        """
        try:
            valid_categories = ["banner", "avatar", "attachment", "document"]
            if category not in valid_categories:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Недопустимая категория файла: {category}. Разрешено: {valid_categories}",
                )

            if file.content_type and not settings.is_file_type_allowed(
                file.content_type, category
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Недопустимый тип файла: {file.content_type}",
                )

            content = await file.read()
            if len(content) > settings.get_max_file_size(category):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Файл слишком большой (макс. {settings.MAX_FILE_SIZE_MB}MB)",
                )

            if self.use_local:
                return await self._upload_local(
                    content=content,
                    filename=file.filename,
                    content_type=file.content_type,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    category=category,
                    uploaded_by=uploaded_by,
                )
            else:
                return await self._upload_s3(
                    content=content,
                    filename=file.filename,
                    content_type=file.content_type,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    category=category,
                    uploaded_by=uploaded_by,
                )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error uploading file: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ошибка загрузки файла: {str(e)}",
            )

    async def _upload_local(
        self,
        content: bytes,
        filename: Optional[str],
        content_type: Optional[str],
        entity_type: str,
        entity_id: int,
        category: str,
        uploaded_by: str,
    ) -> Dict[str, Any]:
        """Загрузка в локальное хранилище"""
        category_path = self.local_path / category
        category_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        original_filename = filename or "unnamed"
        safe_filename = "".join(
            c for c in original_filename if c.isalnum() or c in "._-"
        )
        file_name = f"{entity_id}_{timestamp}_{safe_filename}"
        file_path = category_path / file_name

        with open(file_path, "wb") as buffer:
            buffer.write(content)

        file_url = f"/static/{category}/{file_name}"

        return {
            "file_id": 0,
            "url": file_url,
            "filename": file_name,
            "original_filename": original_filename,
            "size": len(content),
            "content_type": content_type or "application/octet-stream",
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
            "entity_type": entity_type,
            "entity_id": entity_id,
            "category": category,
            "uploaded_by": uploaded_by,
            "file_key": f"{category}/{file_name}",
            "is_public": True,
        }

    async def _upload_s3(
        self,
        content: bytes,
        filename: Optional[str],
        content_type: Optional[str],
        entity_type: str,
        entity_id: int,
        category: str,
        uploaded_by: str,
    ) -> Dict[str, Any]:
        """
        Загрузка в S3-совместимое хранилище (MinIO, AWS S3).

        Генерирует pre-signed URL если бакет приватный.
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        original_filename = filename or "unnamed"
        safe_filename = "".join(
            c for c in original_filename if c.isalnum() or c in "._-"
        )

        file_key = f"{category}/{entity_id}/{timestamp}_{unique_id}_{safe_filename}"

        try:
            put_object_params = {
                "Bucket": self.bucket_name,
                "Key": file_key,
                "Body": content,
                "ContentType": content_type or "application/octet-stream",
                "Metadata": {
                    "entity-type": entity_type,
                    "entity-id": str(entity_id),
                    "category": category,
                    "uploaded-by": uploaded_by,
                },
            }

            if self.public_bucket:
                put_object_params["ACL"] = "public-read"

            self.s3_client.put_object(**put_object_params)
            logger.info(f"File uploaded to S3: {file_key}")

            if self.public_bucket:
                file_url = f"{settings.S3_ENDPOINT_URL}/{self.bucket_name}/{file_key}"
            else:
                file_url = self.s3_client.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": self.bucket_name, "Key": file_key},
                    ExpiresIn=self.url_expiry,
                    HttpMethod="GET",
                )
                logger.debug(
                    f"Generated pre-signed URL (expires in {self.url_expiry}s): {file_url[:100]}..."
                )

            return {
                "file_id": 0,
                "url": file_url,
                "filename": safe_filename,
                "original_filename": original_filename,
                "size": len(content),
                "content_type": content_type or "application/octet-stream",
                "uploaded_at": datetime.now(timezone.utc).isoformat(),
                "entity_type": entity_type,
                "entity_id": entity_id,
                "category": category,
                "uploaded_by": uploaded_by,
                "file_key": file_key,
                "is_public": self.public_bucket,
                "url_expires_at": (
                    None
                    if self.public_bucket
                    else (
                        datetime.now(timezone.utc) + timedelta(seconds=self.url_expiry)
                    ).isoformat()
                ),
            }

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            logger.error(f"S3 ClientError: {error_code} - {str(e)}")

            if error_code == "NoSuchBucket":
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Бакет '{self.bucket_name}' не найден. Создайте его в консоли MinIO.",
                )
            elif error_code == "AccessDenied":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Доступ к хранилищу запрещён. Проверьте S3_ACCESS_KEY и S3_SECRET_KEY.",
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Ошибка хранилища: {error_code}",
                )

        except NoCredentialsError:
            logger.error("S3 credentials not configured")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Не настроены учётные данные для хранилища",
            )
        except Exception as e:
            logger.error(f"Unexpected error uploading to S3: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ошибка загрузки: {str(e)}",
            )

    def get_download_url(self, file_key: str, expires_in: Optional[int] = None) -> str:
        """
        Получение URL для скачивания файла.

        Для приватных бакетов генерирует новый pre-signed URL.

        Args:
            file_key: Ключ файла в хранилище (например: "banner/1/20260220_153000_abc123.jpg")
            expires_in: Время жизни ссылки в секундах (по умолчанию из настроек)

        Returns:
            URL для доступа к файлу
        """
        if self.use_local:
            return f"/static/{file_key}"

        expiry = expires_in or self.url_expiry

        if self.public_bucket:
            return f"{settings.S3_ENDPOINT_URL}/{self.bucket_name}/{file_key}"
        else:
            try:
                url = self.s3_client.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": self.bucket_name, "Key": file_key},
                    ExpiresIn=expiry,
                    HttpMethod="GET",
                )
                return url
            except ClientError as e:
                logger.error(f"Error generating pre-signed URL: {str(e)}")
                raise

    async def delete_file(self, file_key: str) -> bool:
        """
        Удаление файла из хранилища.

        Args:
            file_key: Ключ файла в хранилище

        Returns:
            True если файл удалён, False если не найден или ошибка
        """
        try:
            if self.use_local:
                file_path = self.local_path / file_key
                if file_path.exists():
                    file_path.unlink()
                    logger.info(f"Local file deleted: {file_key}")
                    return True
                logger.warning(f"Local file not found: {file_key}")
                return False
            else:
                self.s3_client.delete_object(Bucket=self.bucket_name, Key=file_key)
                logger.info(f"S3 file deleted: {file_key}")
                return True

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            logger.error(f"Error deleting file {file_key}: {error_code}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting file {file_key}: {str(e)}")
            return False

    def check_bucket_exists(self) -> bool:
        """
        Проверка существования бакета.

        Returns:
            True если бакет существует и доступен
        """
        if self.use_local:
            return self.local_path.exists()

        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            return True
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            logger.error(f"Bucket check failed: {error_code}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error checking bucket: {str(e)}")
            return False

    def validate_file_size(self, file_size: int, category: str = "attachment") -> bool:

        max_size = settings.get_max_file_size(category)
        return file_size <= max_size

    def is_file_type_allowed(
        self, content_type: str, category: str = "attachment"
    ) -> bool:

        return settings.is_file_type_allowed(content_type, category)

    def generate_file_key(
        self, original_filename: str, category: str = "attachment"
    ) -> str:

        from pathlib import Path

        ext = Path(original_filename).suffix.lower()

        if not ext or ext not in settings.ALLOWED_FILE_EXTENSIONS:
            ext = ".bin"

        unique_id = uuid.uuid4().hex

        return f"{category}/{unique_id}{ext}"
