# backend/src/models/user.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from src.database.connection import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    faculty = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# Pydantic модели
from pydantic import BaseModel, ConfigDict
from datetime import datetime

class UserBase(BaseModel):
    student_id: str
    name: str
    faculty: str

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    id: int
    is_admin: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse