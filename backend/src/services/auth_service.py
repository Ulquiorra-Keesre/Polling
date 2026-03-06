# backend/src/services/auth_service.py
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import hashlib

from src.models.user import User, UserRole
from src.models.token import RefreshToken
from src.queries.orm import Repository  # 🔹 Импорт общего Repository
from src.utils.security import (
    create_access_token, 
    create_refresh_token, 
    verify_token, 
    hash_token
)
from src.config import settings


class AuthService:
    """
    Сервис аутентификации — отдельный слой: API → Service → Repository
    
    Инкапсулирует всю логику работы с токенами:
    - Создание пары access/refresh токенов
    - Обновление токенов с ротацией
    - Отзыв сессий (logout)
    - Проверка валидности токенов
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        # 🔹 Используем общий Repository для доступа ко всем репозиториям
        self.repo = Repository(db)
    
    async def authenticate_user(self, student_id: str, name: str, faculty: str) -> Optional[User]:

        # Пытаемся найти существующего пользователя
        user = await self.repo.users.get_by_student_id(student_id)
        
        if not user:
            # Создаём нового пользователя
            admin_student_ids = ["777"]
            role = UserRole.ADMIN if student_id in admin_student_ids else UserRole.USER
            
            user = await self.repo.users.create_user(
                student_id=student_id,
                name=name,
                faculty=faculty,
                role=role
            )
        
        return user
    
    async def create_token_pair(self, user: User, ip_address: str = None, user_agent: str = None) -> dict:

        # 1. Создаём access токен (короткое время жизни)
        access_token = create_access_token(
            data={"sub": user.student_id},
            role=user.role
        )
        
        # 2. Создаём refresh токен (длительное время жизни)
        refresh_token, expires_at = create_refresh_token(user.student_id)
        
        # 3. Сохраняем refresh токен в БД через репозиторий
        await self.repo.refresh_tokens.create_token(
            student_id=user.student_id,
            token_hash=hash_token(refresh_token),
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # 4. Возвращаем пару токенов (refresh токен — только один раз!)
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
                "role": user.role.value if hasattr(user.role, 'value') else str(user.role),
                "created_at": user.created_at.isoformat() if user.created_at else None
            }
        }
    
    
    async def refresh_access_token(self, refresh_token: str, ip_address: str = None) -> Optional[dict]:
        """
        Обновление access токена по refresh токену с ротацией
        
        Алгоритм ротации:
        1. Валидируем refresh токен
        2. Находим запись в БД
        3. Проверяем, не отозван ли и не истёк ли
        4. Отзываем старый refresh токен (is_revoked = True)
        5. Создаём новую пару токенов
        6. Сохраняем новый refresh токен
        
        Args:
            refresh_token: Refresh токен от клиента
            ip_address: IP-адрес для аудита
            
        Returns:
            dict: Новая пара токенов или None при ошибке
        """
        # 1. Проверяем валидность refresh токена
        payload = verify_token(refresh_token, expected_type="refresh")
        if not payload:
            return None
        
        student_id = payload["student_id"]
        token_hash = hash_token(refresh_token)
        
        # 2. Ищем токен в БД через репозиторий
        token_record = await self.repo.refresh_tokens.get_by_hash(token_hash)
        
        # 3. Проверяем, активен ли токен
        if not token_record or token_record.is_revoked:
            return None
        
        # 4. Проверяем, не истёк ли токен
        if token_record.expires_at < datetime.utcnow():
            return None
        
        # 5. Получаем пользователя
        user = await self.repo.users.get_by_student_id(student_id)
        if not user:
            return None
        
        # 6. 🔹 РОТАЦИЯ: Отзываем старый refresh токен
        await self.repo.refresh_tokens.revoke_by_hash(token_hash)
        
        # 7. Создаём новые токены
        new_access_token = create_access_token(
            data={"sub": user.student_id},
            role=user.role
        )
        new_refresh_token, new_expires_at = create_refresh_token(user.student_id)
        
        # 8. Сохраняем новый refresh токен
        await self.repo.refresh_tokens.create_token(
            student_id=student_id,
            token_hash=hash_token(new_refresh_token),
            expires_at=new_expires_at,
            ip_address=ip_address,
            user_agent=token_record.user_agent  # Сохраняем оригинальный User-Agent
        )
        
        # 9. Возвращаем новую пару (только один раз!)
        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
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
    
    
    def check_user_role(self, user: User, allowed_roles: list[UserRole]) -> bool:
       
        user_role = user.role if isinstance(user.role, UserRole) else UserRole(user.role)
        return user_role in allowed_roles
    
    async def check_user_permissions(self, student_id: str, required_role: UserRole) -> bool:
        
        user = await self.get_user_by_id(student_id)
        if not user:
            return False
        
        role_hierarchy = {
            UserRole.GUEST: 0,
            UserRole.USER: 1,
            UserRole.ADMIN: 2
        }
        
        user_level = role_hierarchy.get(user.role if isinstance(user.role, UserRole) else UserRole(user.role), 0)
        required_level = role_hierarchy.get(required_role, 0)
        
        return user_level >= required_level