# backend/src/api/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from src.database.connection import get_db
from src.utils.security import verify_token

# Для JWT аутентификации
security = HTTPBearer()

async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> str:
    """
    Dependency для получения текущего пользователя из JWT токена
    """
    student_id = verify_token(credentials.credentials)
    if not student_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный или просроченный токен",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return student_id


# Тип для аннотаций
DatabaseDep = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[str, Depends(get_current_user)]

async def get_current_admin(
    student_id: Annotated[str, Depends(get_current_user)],
    db: DatabaseDep
) -> str:
    """
    Dependency для проверки, что пользователь - администратор
    """
    admin_student_ids = {"777"}  #Все Админские ID
    
    if student_id not in admin_student_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав. Требуются административные права."
        )
    
    return student_id


CurrentAdmin = Annotated[str, Depends(get_current_admin)]