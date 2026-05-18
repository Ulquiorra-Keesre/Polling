from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from src.models.user import UserRole


class UserRegister(BaseModel):
    student_id: str = Field(..., min_length=3, max_length=20)
    password: str = Field(..., min_length=6, max_length=100)
    name: str = Field(..., min_length=2, max_length=100)
    faculty: str = Field(..., min_length=2, max_length=200)
    role: Optional[str] = "user"


class UserLogin(BaseModel):
    student_id: str = Field(..., min_length=3, max_length=20)
    password: str = Field(..., min_length=6, max_length=100)


class UserResponse(BaseModel):
    id: int
    student_id: str
    name: str
    faculty: str
    role: UserRole
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse
