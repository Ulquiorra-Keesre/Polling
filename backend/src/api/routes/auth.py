from fastapi import APIRouter, HTTPException, status, Request
from src.models.user import UserRole
from src.services.auth_service import AuthService
from src.api.dependencies import DatabaseDep, CurrentUser, CurrentAdmin
from src.schemas.user import Token, UserRegister, UserLogin, UserUpdateRole

router = APIRouter()


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, db: DatabaseDep):
    """
    Регистрация нового пользователя
    """
    try:
        auth_service = AuthService(db)

        user = await auth_service.register(user_data)

        tokens = await auth_service.create_token_pair(user)

        return tokens

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, db: DatabaseDep):
    """
    Вход в систему
    """
    try:
        auth_service = AuthService(db)

        user = await auth_service.authenticate(
            credentials.student_id, credentials.password
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный номер студенческого или пароль",
                headers={"WWW-Authenticate": "Bearer"},
            )

        tokens = await auth_service.create_token_pair(user)

        return tokens

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка входа: {str(e)}",
        )


@router.post("/refresh", status_code=status.HTTP_200_OK)
async def refresh_token(db: DatabaseDep, request: Request, refresh_token: str = None):
    try:
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Refresh token не предоставлен",
            )

        auth_service = AuthService(db)

        tokens = await auth_service.refresh_access_token(
            refresh_token=refresh_token,
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
            detail=f"Ошибка обновления токена: {str(e)}",
        )


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(db: DatabaseDep, current_user: CurrentUser):
    """
    Завершение сессии
    Отзывает все refresh токены пользователя
    """
    try:
        auth_service = AuthService(db)
        await auth_service.revoke_all_tokens(current_user["student_id"])

        return {"success": True, "message": "Сессия завершена"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Ошибка выхода: {str(e)}"
        )


@router.get("/me", status_code=status.HTTP_200_OK)
async def get_current_user_info(current_user: CurrentUser):
    """
    Получить информацию о текущем пользователе
    """
    user = current_user["user"]
    return {
        "id": user.id,
        "student_id": user.student_id,
        "name": user.name,
        "faculty": user.faculty,
        "role": user.role.value if hasattr(user.role, "value") else str(user.role),
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


@router.patch("/users/{student_id}/role", status_code=status.HTTP_200_OK)
async def update_user_role_endpoint(
    student_id: str,
    role_data: UserUpdateRole,
    db: DatabaseDep,
    current_admin: CurrentAdmin,
):
    from src.queries.users import update_user_role

    if student_id == current_admin["student_id"] and role_data.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Администратор не может понизить свои права через API",
        )

    updated_user = await update_user_role(db, student_id, role_data.role)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден"
        )

    return {
        "success": True,
        "message": f"Роль пользователя {student_id} изменена на {role_data.role.value}",
        "user": updated_user,
    }


@router.get("/users", status_code=status.HTTP_200_OK)
async def get_all_users_endpoint(db: DatabaseDep, current_admin: CurrentAdmin):
    from src.queries.users import get_all_users

    users = await get_all_users(db)
    return {"success": True, "count": len(users), "users": users}
