from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from src.database.connection import Base
import enum


class UserRole(enum.Enum):
    GUEST = "guest"
    USER = "user"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    faculty = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    votes = relationship("Vote", back_populates="user", cascade="all, delete-orphan")
    refresh_tokens = relationship(
        "RefreshToken", back_populates="user", cascade="all, delete-orphan"
    )
    uploaded_files = relationship(
        "FileMetadata", back_populates="uploader", cascade="all, delete-orphan"
    )


from pydantic import BaseModel, ConfigDict
from datetime import datetime


class UserBase(BaseModel):
    student_id: str
    name: str
    faculty: str


class UserCreate(UserBase):
    pass


class UserResponse(BaseModel):
    id: int
    student_id: str
    name: str
    faculty: str
    role: str
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True, "use_enum_values": True}


class UserUpdateRole(BaseModel):
    role: UserRole
    model_config = ConfigDict(use_enum_values=True)


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: Optional[int] = None
    user: UserResponse
