from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from src.models.user import UserCreate, Token
from src.queries.users import get_or_create_user
from src.utils.security import create_access_token
from src.api.dependencies import DatabaseDep, get_current_user

router = APIRouter()

@router.post("/login", response_model=Token, status_code=status.HTTP_200_OK)
async def login(
    user_data: UserCreate,
    db: DatabaseDep
):
    """
    Авторизация пользователя по номеру студенческого билета
    """
    try:
        # Получаем или создаем пользователя
        user = await get_or_create_user(db, user_data)
        
        # Создаем JWT токен
        access_token = create_access_token(data={"sub": user.student_id})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка авторизации: {str(e)}"
        )

@router.get("/me")
async def get_current_user_info(
    db: DatabaseDep,
    student_id: Annotated[str, Depends(get_current_user)]
):
    """
    Получить информацию о текущем пользователе
    """
    from src.queries.users import get_user_by_student_id
    
    user = await get_user_by_student_id(db, student_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    return user