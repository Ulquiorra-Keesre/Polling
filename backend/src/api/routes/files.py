import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form

from src.services.file_service import FileService
from src.api.dependencies import DatabaseDep, CurrentUser
from src.models.file import FileMetadata
from src.schemas.file import (
    FileUploadResponse,
    FileInfo,
    FileDownloadResponse,
    FileDeleteResponse,
    FileListResponse,
)
from src.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Files"])


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    db: DatabaseDep,
    current_user: CurrentUser,
    file: UploadFile = File(...),
    entity_type: str = Form(...),
    entity_id: int = Form(...),
    category: str = Form("attachment"),
):
    """
    Загрузка файла и привязка к сущности.

    - **entity_type**: Тип сущности (poll, user, option)
    - **entity_id**: ID сущности
    - **category**: Категория файла (banner, avatar, attachment, document)

    Возвращает pre-signed URL если бакет приватный.
    """
    try:
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Требуется авторизация"
            )

        valid_entity_types = ["poll", "user", "option"]
        if entity_type not in valid_entity_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Недопустимый тип сущности. Разрешено: {valid_entity_types}",
            )

        if entity_type == "poll" and current_user.get("role") != "admin":
            pass

        file_service = FileService()
        upload_result = await file_service.upload_file(
            file=file,
            entity_type=entity_type,
            entity_id=entity_id,
            category=category,
            uploaded_by=current_user.get("student_id") or str(current_user.get("id")),
        )

        file_meta = FileMetadata(
            entity_type=entity_type,
            entity_id=entity_id,
            category=category,
            file_key=upload_result["file_key"],
            original_filename=upload_result["original_filename"],
            content_type=upload_result["content_type"],
            size_bytes=upload_result["size"],
            uploaded_by=upload_result["uploaded_by"],
        )
        db.add(file_meta)
        await db.commit()
        await db.refresh(file_meta)

        upload_result["file_id"] = file_meta.id

        logger.info(
            f"File uploaded: {upload_result['file_key']} by {current_user.get('student_id')}"
        )

        return FileUploadResponse(**upload_result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in upload_file endpoint: {str(e)}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при загрузке файла: {str(e)}",
        )


@router.get("/{file_id}", response_model=FileInfo)
async def get_file_info(file_id: int, db: DatabaseDep, current_user: CurrentUser):
    """Получение информации о файле"""
    try:
        file_meta = await db.get(FileMetadata, file_id)
        if not file_meta:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Файл не найден"
            )

        if (
            file_meta.uploaded_by != current_user.get("student_id")
            and current_user.get("role") != "admin"
        ):
            if file_meta.category not in ["banner", "avatar"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Недостаточно прав для просмотра этого файла",
                )

        file_service = FileService()
        current_url = file_service.get_download_url(file_meta.file_key)

        return FileInfo(
            file_id=file_meta.id,
            entity_type=file_meta.entity_type,
            entity_id=file_meta.entity_id,
            category=file_meta.category,
            filename=file_meta.original_filename,
            original_filename=file_meta.original_filename,
            content_type=file_meta.content_type,
            size=file_meta.size_bytes,
            size_formatted=f"{file_meta.size_bytes / 1024 / 1024:.2f} MB",
            uploaded_by=file_meta.uploaded_by,
            uploaded_at=file_meta.uploaded_at,
            url=current_url,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting file info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении информации: {str(e)}",
        )


@router.get("/{file_id}/download", response_model=FileDownloadResponse)
async def download_file(file_id: int, db: DatabaseDep, current_user: CurrentUser):
    """
    Получение pre-signed URL для скачивания файла.

    Возвращает временную ссылку, действительную {S3_URL_EXPIRY_SECONDS} секунд.
    """
    try:
        file_meta = await db.get(FileMetadata, file_id)
        if not file_meta:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Файл не найден"
            )

        if (
            file_meta.uploaded_by != current_user.get("student_id")
            and current_user.get("role") != "admin"
        ):
            if file_meta.category not in ["banner", "avatar"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Недостаточно прав для скачивания",
                )

        file_service = FileService()
        download_url = file_service.get_download_url(
            file_key=file_meta.file_key, expires_in=settings.S3_URL_EXPIRY_SECONDS
        )

        return FileDownloadResponse(
            file_id=file_meta.id,
            filename=file_meta.original_filename,
            url=download_url,
            expires_in=settings.S3_URL_EXPIRY_SECONDS,
            content_type=file_meta.content_type,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating download URL: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при генерации ссылки: {str(e)}",
        )


@router.delete("/{file_id}", response_model=FileDeleteResponse)
async def delete_file(file_id: int, db: DatabaseDep, current_user: CurrentUser):
    """Удаление файла (только загрузивший пользователь или админ)"""
    try:
        file_meta = await db.get(FileMetadata, file_id)
        if not file_meta:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Файл не найден"
            )

        if (
            file_meta.uploaded_by != current_user.get("student_id")
            and current_user.get("role") != "admin"
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для удаления",
            )

        file_service = FileService()
        deleted = await file_service.delete_file(file_meta.file_key)
        if not deleted:
            logger.warning(f"File storage deletion failed: {file_meta.file_key}")

        await db.delete(file_meta)
        await db.commit()

        logger.info(f"File deleted: {file_id} by {current_user.get('student_id')}")

        return FileDeleteResponse(
            success=True, message="Файл успешно удалён", file_id=file_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting file: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при удалении файла: {str(e)}",
        )


@router.get("/", response_model=FileListResponse)
async def list_files(
    db: DatabaseDep,
    current_user: CurrentUser,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    category: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
):
    """Получение списка файлов с фильтрацией"""
    try:
        from sqlalchemy import select, func

        query = select(FileMetadata)

        if entity_type:
            query = query.where(FileMetadata.entity_type == entity_type)
        if entity_id:
            query = query.where(FileMetadata.entity_id == entity_id)
        if category:
            query = query.where(FileMetadata.category == category)

        if current_user.get("role") != "admin":
            query = query.where(
                FileMetadata.uploaded_by == current_user.get("student_id")
            )

        total_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(total_query)
        total = total_result.scalar() or 0

        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)

        result = await db.execute(query)
        files_meta = result.scalars().all()

        file_service = FileService()
        file_infos = []
        for fm in files_meta:
            file_infos.append(
                FileInfo(
                    file_id=fm.id,
                    entity_type=fm.entity_type,
                    entity_id=fm.entity_id,
                    category=fm.category,
                    filename=fm.original_filename,
                    original_filename=fm.original_filename,
                    content_type=fm.content_type,
                    size=fm.size_bytes,
                    size_formatted=f"{fm.size_bytes / 1024 / 1024:.2f} MB",
                    uploaded_by=fm.uploaded_by,
                    uploaded_at=fm.uploaded_at,
                    url=file_service.get_download_url(fm.file_key),
                )
            )

        return FileListResponse(
            items=file_infos,
            total=total,
            page=page,
            limit=limit,
            pages=(total + limit - 1) // limit,
        )

    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении списка файлов: {str(e)}",
        )


@router.get("/config")
async def get_file_storage_config():
    """
    Публичные настройки файлового хранилища.

    Этот эндпоинт НЕ требует авторизации и возвращает
    только безопасные для клиента настройки.
    """
    return {
        "maxFileSizeMb": settings.MAX_FILE_SIZE_MB,
        "allowedTypes": settings.ALLOWED_FILE_TYPES,
        "allowedExtensions": settings.ALLOWED_FILE_EXTENSIONS,
        "isPublicBucket": settings.S3_PUBLIC_BUCKET,
        "urlExpirySeconds": settings.S3_URL_EXPIRY_SECONDS
        if not settings.S3_PUBLIC_BUCKET
        else None,
        "categories": ["banner", "avatar", "attachment", "document"],
    }
