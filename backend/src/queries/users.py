# backend/src/queries/users.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models.user import User
from src.models.user import UserCreate, UserResponse

async def create_user(db: AsyncSession, user: UserCreate, is_admin: bool = False) -> UserResponse:
    """Создать нового пользователя"""
    db_user = User(
        student_id=user.student_id,
        name=user.name,
        faculty=user.faculty,
        is_admin=is_admin
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return UserResponse.model_validate(db_user)

async def get_user_by_student_id(db: AsyncSession, student_id: str) -> UserResponse | None:
    """Найти пользователя по student_id"""
    result = await db.execute(
        select(User).where(User.student_id == student_id)
    )
    user = result.scalar_one_or_none()
    return UserResponse.model_validate(user) if user else None

async def get_or_create_user(db: AsyncSession, user_data: UserCreate) -> UserResponse:
    """Получить или создать пользователя"""
    user = await get_user_by_student_id(db, user_data.student_id)
    if not user:
        user = await create_user(db, user_data)
    return user

async def is_admin(db: AsyncSession, student_id: str) -> bool:
    """Проверить, является ли пользователь администратором"""
    user = await get_user_by_student_id(db, student_id)
    return user.is_admin if user else False