from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from src.queries.orm import Repository
from src.models.user import User, UserCreate, UserResponse, UserRole

async def create_user(db: AsyncSession, user: UserCreate, role: UserRole = UserRole.USER) -> UserResponse:
    repo = Repository(db)
    admin_student_ids = ["777"]
    user_role = role
    if user.student_id in admin_student_ids:
        user_role = UserRole.ADMIN
    
    db_user = await repo.users.create_user(
        student_id=user.student_id,
        name=user.name,
        faculty=user.faculty,
        role=user_role
    )
    return UserResponse.model_validate(db_user)

async def get_user_by_student_id(db: AsyncSession, student_id: str) -> UserResponse | None:
    repo = Repository(db)
    user = await repo.users.get_by_student_id(student_id)
    return UserResponse.model_validate(user) if user else None

async def get_or_create_user(db: AsyncSession, user_data: UserCreate) -> UserResponse:
    repo = Repository(db)
    user = await repo.users.get_by_student_id(user_data.student_id)
    if not user:
        admin_student_ids = ["777"]
        user_role = UserRole.USER
        if user_data.student_id in admin_student_ids:
            user_role = UserRole.ADMIN
        user = await repo.users.create_user(
            student_id=user_data.student_id,
            name=user_data.name,
            faculty=user_data.faculty,
            role=user_role
        )
    return UserResponse.model_validate(user)

async def is_admin(db: AsyncSession, student_id: str) -> bool:
    repo = Repository(db)
    user = await repo.users.get_by_student_id(student_id)
    return user.role == UserRole.ADMIN if user else False


async def get_all_users(db: AsyncSession):
    repo = Repository(db)
    users = await repo.users.get_all()
    return [UserResponse.model_validate(user) for user in users]

async def update_user_role(db: AsyncSession, student_id: str, new_role: UserRole) -> UserResponse | None:
    repo = Repository(db)
    updated_user = await repo.users.update_user_role(student_id, new_role)
    return UserResponse.model_validate(updated_user) if updated_user else None

async def get_users_by_role(db: AsyncSession, role: UserRole) -> list:
    repo = Repository(db)
    users = await repo.users.get_many_by_field("role", role)
    return [UserResponse.model_validate(user) for user in users]

# async def update_user_admin_status(db: AsyncSession, student_id: str, is_admin: bool) -> UserResponse | None:
#     """Обновить статус администратора"""
#     repo = Repository(db)
    
#     user = await repo.users.get_by_student_id(student_id)
#     if user:
#         updated_user = await repo.users.update(user.id, is_admin=is_admin)
#         return UserResponse.model_validate(updated_user)
#     return None