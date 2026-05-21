# src/schemas/user.py
"""Pydantic-схемы для пользователей (совместимо с Pydantic v2)"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

from src.models.user import UserRole  # ← Импорт Enum из models (без циклических проблем)


class UserRegister(BaseModel):
    """Схема регистрации пользователя"""
    student_id: str = Field(..., min_length=3, max_length=20, description="ID студента")
    password: str = Field(..., min_length=6, max_length=100, description="Пароль")
    name: str = Field(..., min_length=2, max_length=100, description="Имя пользователя")
    faculty: str = Field(..., min_length=2, max_length=200, description="Факультет")
    role: Optional[str] = Field(default="user", description="Роль (по умолчанию: user)")


class UserLogin(BaseModel):
    """Схема входа"""
    student_id: str = Field(..., min_length=3, max_length=20)
    password: str = Field(..., min_length=6, max_length=100)


class UserResponse(BaseModel):
    """Схема ответа с данными пользователя"""
    id: int
    student_id: str
    name: str
    faculty: str
    role: UserRole  # ← Строгая типизация через Enum
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)  # ✅ Pydantic v2 style


class Token(BaseModel):
    """Схема токена доступа"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse

    model_config = ConfigDict(from_attributes=True)