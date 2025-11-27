# backend/src/queries/users.py
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from src.queries.orm import Repository
from src.models.user import User, UserCreate, UserResponse

async def create_user(db: AsyncSession, user: UserCreate, is_admin: bool = False) -> UserResponse:
    """Создать нового пользователя"""
    repo = Repository(db)
    
    db_user = await repo.users.create_user(
        student_id=user.student_id,
        name=user.name,
        faculty=user.faculty,
        is_admin=is_admin
    )
    return UserResponse.model_validate(db_user)

async def get_user_by_student_id(db: AsyncSession, student_id: str) -> UserResponse | None:
    """Найти пользователя по student_id"""
    repo = Repository(db)
    
    user = await repo.users.get_by_student_id(student_id)
    return UserResponse.model_validate(user) if user else None

async def get_or_create_user(db: AsyncSession, user_data: UserCreate) -> UserResponse:
    """Получить или создать пользователя"""
    repo = Repository(db)
    
    user = await repo.users.get_by_student_id(user_data.student_id)
    if not user:
        user = await repo.users.create_user(
            student_id=user_data.student_id,
            name=user_data.name,
            faculty=user_data.faculty,
            is_admin=False
        )
    return UserResponse.model_validate(user)

async def is_admin(db: AsyncSession, student_id: str) -> bool:
    """Проверить, является ли пользователь администратором"""
    repo = Repository(db)
    
    user = await repo.users.get_by_student_id(student_id)
    return user.is_admin if user else False


async def get_all_users(db: AsyncSession):
    """Получить всех пользователей"""
    repo = Repository(db)
    
    users = await repo.users.get_all()
    return [UserResponse.model_validate(user) for user in users]

async def update_user_admin_status(db: AsyncSession, student_id: str, is_admin: bool) -> UserResponse | None:
    """Обновить статус администратора"""
    repo = Repository(db)
    
    user = await repo.users.get_by_student_id(student_id)
    if user:
        updated_user = await repo.users.update(user.id, is_admin=is_admin)
        return UserResponse.model_validate(updated_user)
    return None