# src/models/user.py
"""SQLAlchemy модели для пользователей"""

from typing import TYPE_CHECKING, List
from sqlalchemy import Column, Integer, String, DateTime, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from src.database.connection import Base
import enum

# 🔹 Для типизации циклических импортов (mypy/ruff)
if TYPE_CHECKING:
    from src.models.vote import Vote
    from src.models.token import RefreshToken
    from src.models.file import FileMetadata


class UserRole(enum.Enum):
    """Роли пользователей"""
    GUEST = "guest"
    USER = "user"
    ADMIN = "admin"


class User(Base):
    """Модель пользователя"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    faculty = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 🔹 Связи (используем строки + TYPE_CHECKING для избежания циклических импортов)
    votes: List["Vote"] = relationship(
        "Vote",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="select"
    )
    refresh_tokens: List["RefreshToken"] = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="select"
    )
    uploaded_files: List["FileMetadata"] = relationship(
        "FileMetadata",
        back_populates="uploader",
        cascade="all, delete-orphan",
        lazy="select"
    )