from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from passlib.context import CryptContext

from src.models.user import User, UserRole
from src.queries.orm import Repository
from src.utils.security import (
    create_access_token,
    create_refresh_token,
    verify_token,
    hash_token,
)
from src.config import settings
from src.schemas.user import UserRegister

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


class AuthService:
    """Сервис аутентификации — отдельный слой: API → Service → Repository"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = Repository(db)

    def hash_password(self, password: str) -> str:
        if not isinstance(password, str):
            password = str(password)
        if len(password.encode("utf-8")) > 72:
            password_bytes = password.encode("utf-8")[:72]
            password = password_bytes.decode("utf-8", errors="ignore")
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    async def register(self, user_data: UserRegister) -> User:
        """Регистрация нового пользователя с правильной ролью"""
        user = await self.repo.users.get_by_student_id(user_data.student_id)
        if user:
            raise ValueError(
                "Пользователь с таким номером студенческого уже существует"
            )

        hashed_password = self.hash_password(user_data.password)

        input_role = getattr(user_data, "role", None)
        if input_role is None:
            role = UserRole.USER
        elif isinstance(input_role, UserRole):
            role = input_role
        elif isinstance(input_role, str):
            role_str = input_role.strip().lower()
            if role_str == "admin":
                role = UserRole.ADMIN
            elif role_str == "guest":
                role = UserRole.GUEST
            else:
                role = UserRole.USER
        else:
            role = UserRole.USER

        new_user = User(
            student_id=user_data.student_id,
            name=user_data.name,
            faculty=user_data.faculty,
            password_hash=hashed_password,
            role=role,
        )

        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)
        return new_user

    async def authenticate(self, student_id: str, password: str) -> Optional[User]:
        user = await self.repo.users.get_by_student_id(student_id)
        if not user:
            return None
        if not self.verify_password(password, user.password_hash):
            return None
        return user

    async def create_token_pair(
        self, user: User, user_agent: Optional[str] = None
    ) -> dict:
        """Создать пару access/refresh токенов"""
        role_value = user.role.value if hasattr(user.role, "value") else str(user.role)

        access_token = create_access_token(
            data={"sub": user.student_id}, role=role_value
        )

        refresh_token, expires_at = create_refresh_token(user.student_id)

        await self.repo.refresh_tokens.create_token(
            student_id=user.student_id,
            token_hash=hash_token(refresh_token),
            expires_at=expires_at,
            user_agent=user_agent,
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "id": user.id,
                "student_id": user.student_id,
                "name": user.name,
                "faculty": user.faculty,
                "role": role_value,
                "created_at": user.created_at.isoformat() if user.created_at else None,
            },
        }

    async def refresh_access_token(
        self, refresh_token: str, user_agent: Optional[str] = None
    ) -> Optional[dict]:
        """Обновление access токена по refresh токену с ротацией"""
        payload = verify_token(refresh_token, expected_type="refresh")
        if not payload:
            return None

        student_id = payload["student_id"]
        token_hash = hash_token(refresh_token)

        token_record = await self.repo.refresh_tokens.get_by_hash(token_hash)
        if not token_record or token_record.is_revoked:
            return None

        now = datetime.now(timezone.utc)
        if token_record.expires_at < now:
            return None

        user = await self.repo.users.get_by_student_id(student_id)
        if not user:
            return None

        await self.repo.refresh_tokens.revoke_by_hash(token_hash)

        role_value = user.role.value if hasattr(user.role, "value") else str(user.role)
        new_access_token = create_access_token(
            data={"sub": user.student_id}, role=role_value
        )
        new_refresh_token, new_expires_at = create_refresh_token(user.student_id)

        await self.repo.refresh_tokens.create_token(
            student_id=student_id,
            token_hash=hash_token(new_refresh_token),
            expires_at=new_expires_at,
            user_agent=user_agent,
        )

        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

    async def revoke_all_tokens(self, student_id: str) -> bool:
        revoked_count = await self.repo.refresh_tokens.revoke_all_for_user(student_id)
        return revoked_count > 0

    async def revoke_token(self, token_hash: str) -> bool:
        return await self.repo.refresh_tokens.revoke_by_hash(token_hash)

    async def get_user_by_id(self, student_id: str) -> Optional[User]:
        return await self.repo.users.get_by_student_id(student_id)

    async def get_active_tokens_count(self, student_id: str) -> int:
        tokens = await self.repo.refresh_tokens.get_active_by_student_id(student_id)
        return len(tokens)

    async def cleanup_expired_tokens(self) -> int:
        return await self.repo.refresh_tokens.cleanup_expired()

    def check_user_role(self, user: User, allowed_roles: List[UserRole]) -> bool:
        user_role = (
            user.role if isinstance(user.role, UserRole) else UserRole(user.role)
        )
        return user_role in allowed_roles

    async def check_user_permissions(
        self, student_id: str, required_role: UserRole
    ) -> bool:
        user = await self.get_user_by_id(student_id)
        if not user:
            return False

        role_hierarchy = {UserRole.GUEST: 0, UserRole.USER: 1, UserRole.ADMIN: 2}
        user_role = (
            user.role if isinstance(user.role, UserRole) else UserRole(user.role)
        )
        user_level = role_hierarchy.get(user_role, 0)
        required_level = role_hierarchy.get(required_role, 0)

        return user_level >= required_level
