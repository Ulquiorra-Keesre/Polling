from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List
from datetime import datetime
from enum import Enum


class FileCategory(str, Enum):
    """Категории файлов для привязки к сущностям"""

    BANNER = "banner"
    AVATAR = "avatar"
    ATTACHMENT = "attachment"
    DOCUMENT = "document"


class FileType(str, Enum):
    """Типы файлов по MIME-type"""

    IMAGE_JPEG = "image/jpeg"
    IMAGE_PNG = "image/png"
    IMAGE_GIF = "image/gif"
    IMAGE_WEBP = "image/webp"
    PDF = "application/pdf"
    DOC = "application/msword"
    DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    XLS = "application/vnd.ms-excel"
    XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


class FileUploadParams(BaseModel):
    """Параметры для загрузки файла"""

    entity_type: str = Field(
        ..., min_length=1, max_length=50, description="Тип сущности (poll, user, etc.)"
    )
    entity_id: int = Field(..., ge=1, description="ID сущности")
    category: FileCategory = Field(
        default=FileCategory.ATTACHMENT, description="Категория файла"
    )

    @field_validator("entity_type")
    @classmethod
    def validate_entity_type(cls, v: str) -> str:
        allowed_types = ["poll", "user", "option"]
        if v.lower() not in allowed_types:
            raise ValueError(f"Недопустимый тип сущности. Разрешено: {allowed_types}")
        return v.lower()


class FileUploadResponse(BaseModel):
    """Ответ после успешной загрузки файла"""

    success: bool = True
    file_id: int
    url: str
    filename: str
    size: int
    content_type: str
    uploaded_at: datetime
    entity_type: str
    entity_id: int
    category: str

    model_config = ConfigDict(from_attributes=True)


class FileInfo(BaseModel):
    """Полная информация о файле"""

    file_id: int
    entity_type: str
    entity_id: int
    category: str
    filename: str
    original_filename: str
    content_type: str
    size: int
    size_formatted: Optional[str] = None
    uploaded_by: str
    uploaded_at: datetime
    url: Optional[str] = None
    download_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("size")
    @classmethod
    def validate_size(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Размер файла не может быть отрицательным")
        return v


class FileMetadata(BaseModel):
    """Метаданные файла (без URL)"""

    id: int
    entity_type: str
    entity_id: int
    category: str
    file_key: str
    original_filename: str
    content_type: str
    size_bytes: int
    uploaded_by: str
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FileListResponse(BaseModel):
    """Список файлов с пагинацией"""

    items: List[FileInfo]
    total: int
    page: int
    limit: int
    pages: int

    model_config = ConfigDict(from_attributes=True)


class FileDownloadResponse(BaseModel):
    """Ответ для скачивания файла (pre-signed URL)"""

    file_id: int
    filename: str
    url: str
    expires_in: int = Field(default=300, description="Время действия ссылки в секундах")
    content_type: str

    model_config = ConfigDict(from_attributes=True)


class FileDeleteResponse(BaseModel):
    """Ответ после удаления файла"""

    success: bool
    message: str
    file_id: int

    model_config = ConfigDict(from_attributes=True)


class FileConstraints(BaseModel):
    """Ограничения на загрузку файлов"""

    max_size_mb: int = Field(default=10, description="Максимальный размер в МБ")
    max_size_bytes: int = Field(
        default=10485760, description="Максимальный размер в байтах"
    )
    allowed_types: List[str] = Field(
        default=[
            "image/jpeg",
            "image/png",
            "image/gif",
            "image/webp",
            "application/pdf",
        ],
        description="Разрешённые MIME-типы",
    )
    allowed_extensions: List[str] = Field(
        default=[".jpg", ".jpeg", ".png", ".gif", ".webp", ".pdf"],
        description="Разрешённые расширения",
    )

    model_config = ConfigDict(from_attributes=True)


class FileUploadProgress(BaseModel):
    """Прогресс загрузки файла (для WebSocket/streaming)"""

    file_id: Optional[int] = None
    filename: str
    uploaded_bytes: int
    total_bytes: int
    percentage: float
    status: str = Field(default="uploading")
    error: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("percentage")
    @classmethod
    def validate_percentage(cls, v: float) -> float:
        if not 0 <= v <= 100:
            raise ValueError("Процент должен быть от 0 до 100")
        return v


class FileEntityRelation(BaseModel):
    """Связь файла с сущностью"""

    file_id: int
    entity_type: str
    entity_id: int
    category: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
