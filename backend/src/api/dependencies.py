from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated, List

from src.database.connection import get_db
from src.utils.security import verify_token
from src.services.auth_service import AuthService
from src.models.user import UserRole
from datetime import datetime

security = HTTPBearer()

async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> dict:
    """
    Dependency для получения текущего пользователя из access токена
    """
    token_data = verify_token(credentials.credentials, expected_type="access")
    
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный или просроченный токен",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if token_data.get("exp", 0) < datetime.utcnow().timestamp():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Токен истёк",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    auth_service = AuthService(db)
    user = await auth_service.get_user_by_id(token_data["student_id"])
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return {
        "student_id": token_data["student_id"],
        "role": user.role.value if hasattr(user.role, 'value') else str(user.role),
        "user": user
    }

def require_role(allowed_roles: List[UserRole]):
    """
    Factory для создания dependency проверки роли
    """
    async def role_checker(
        current_user: Annotated[dict, Depends(get_current_user)]
    ) -> dict:
        if current_user["role"] not in [r.value if hasattr(r, 'value') else str(r) for r in allowed_roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Недостаточно прав. Требуется одна из ролей: {[r.value if hasattr(r, 'value') else str(r) for r in allowed_roles]}"
            )
        return current_user
    return role_checker

#Типы для аннотаций
DatabaseDep = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[dict, Depends(get_current_user)]
CurrentAdmin = Annotated[dict, Depends(require_role([UserRole.ADMIN]))]
CurrentUserOrAdmin = Annotated[dict, Depends(require_role([UserRole.USER, UserRole.ADMIN]))]

# async def get_current_admin(
#     student_id: Annotated[str, Depends(get_current_user)],
#     db: DatabaseDep
# ) -> str:
    
    #Dependency для проверки, что пользователь - администратор
    
    # admin_student_ids = {"777"}  #Все Админские ID
    
    # if student_id not in admin_student_ids:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Недостаточно прав. Требуются административные права."
    #     )