from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from src.models.user import UserCreate, Token, UserUpdateRole, UserRole
from src.queries.users import get_or_create_user
from src.utils.security import create_access_token
from src.api.dependencies import DatabaseDep, get_current_user, CurrentAdmin

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
        access_token = create_access_token(data={"sub": user.student_id}, role=user.role)
        
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

@router.patch("/users/{student_id}/role", status_code=status.HTTP_200_OK)
async def update_user_role_endpoint(
    student_id: str,
    role_data: UserUpdateRole,
    db: DatabaseDep,
    current_admin: CurrentAdmin
):
    """
    Изменить роль пользователя (только для администраторов)
    """
    from src.queries.users import update_user_role
    
    if student_id == current_admin["student_id"] and role_data.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Администратор не может понизить свои права через API"
        )
    
    updated_user = await update_user_role(db, student_id, role_data.role)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    return {
        "success": True,
        "message": f"Роль пользователя {student_id} изменена на {role_data.role.value}",
        "user": updated_user
    }