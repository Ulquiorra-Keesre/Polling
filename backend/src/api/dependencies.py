from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated, List

from src.database.connection import get_db
from src.utils.security import verify_token
from src.queries.users import get_user_by_student_id
from src.models.user import UserRole

security = HTTPBearer()

async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> dict:
    token_data = verify_token(credentials.credentials)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный или просроченный токен",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = await get_user_by_student_id(db, token_data["student_id"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return {
        "student_id": token_data["student_id"],
        "role": user.role if hasattr(user, 'role') else UserRole.USER
    }

def require_role(allowed_roles: List[UserRole]):
    async def role_checker(
        current_user: Annotated[dict, Depends(get_current_user)]
    ) -> dict:
        if current_user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Недостаточно прав. Требуется одна из ролей: {[r.value for r in allowed_roles]}"
            )
        return current_user
    return role_checker


# Тип для аннотаций
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