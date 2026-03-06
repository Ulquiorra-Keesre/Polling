# backend/src/api/routes/auth.py
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from src.models.user import UserCreate, UserUpdateRole, UserRole
from src.services.auth_service import AuthService
from src.api.dependencies import DatabaseDep, CurrentUser, CurrentAdmin
from src.utils.security import hash_token

router = APIRouter()


@router.post("/login", status_code=status.HTTP_200_OK)
async def login(
    user_data: UserCreate,
    db: DatabaseDep,
    request: Request
):
    """
    пара access и refresh токенов
    """
    try:
        auth_service = AuthService(db)
        
        user = await auth_service.authenticate_user(
            student_id=user_data.student_id,
            name=user_data.name,
            faculty=user_data.faculty
        )
        
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent", None)
        
        tokens = await auth_service.create_token_pair(
            user=user,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return tokens
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка авторизации: {str(e)}"
        )


@router.post("/refresh", status_code=status.HTTP_200_OK)
async def refresh_token(
    db: DatabaseDep,
    request: Request,
    refresh_token: str = None
):
    """
    Обновление access токена через refresh токен
    Тело запроса: {"refresh_token": "..."}
    Или заголовок: Authorization: Bearer <refresh_token>
    """
    try:
        if not refresh_token:
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                refresh_token = auth_header[7:]
        
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Refresh token не предоставлен"
            )
        
        auth_service = AuthService(db)
        ip_address = request.client.host if request.client else None
        
        tokens = await auth_service.refresh_access_token(
            refresh_token=refresh_token,
            ip_address=ip_address
        )
        
        if not tokens:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token истёк или был отозван",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return tokens
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка обновления токена: {str(e)}"
        )


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    db: DatabaseDep,
    current_user: CurrentUser
):
    """
    Завершение сессии
    Отзывает все refresh токены пользователя
    """
    try:
        auth_service = AuthService(db)
        await auth_service.revoke_all_tokens(current_user["student_id"])
        
        return {
            "success": True,
            "message": "Сессия завершена"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка выхода: {str(e)}"
        )


@router.get("/me", status_code=status.HTTP_200_OK)
async def get_current_user_info(
    current_user: CurrentUser
):
    """
    Получить информацию о текущем пользователе
    """
    user = current_user["user"]
    return {
        "id": user.id,
        "student_id": user.student_id,
        "name": user.name,
        "faculty": user.faculty,
        "role": user.role.value if hasattr(user.role, 'value') else str(user.role),
        "created_at": user.created_at.isoformat() if user.created_at else None
    }


@router.patch("/users/{student_id}/role", status_code=status.HTTP_200_OK)
async def update_user_role_endpoint(
    student_id: str,
    role_data: UserUpdateRole,
    db: DatabaseDep,
    current_admin: CurrentAdmin
):
    #Изменить роль пользователя (только для администратор имеет права доступа)
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


@router.get("/users", status_code=status.HTTP_200_OK)
async def get_all_users_endpoint(
    db: DatabaseDep,
    current_admin: CurrentAdmin
):
    #Получить список всех пользователей (только для администратор имеет права доступа)
    from src.queries.users import get_all_users
    users = await get_all_users(db)
    return {"success": True, "count": len(users), "users": users}