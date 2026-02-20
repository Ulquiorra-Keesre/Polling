from datetime import datetime, timedelta
from jose import JWTError, jwt
from src.config import settings
from src.models.user import UserRole  # Импорт enum

def create_access_token(data: dict, role: UserRole | str = UserRole.USER):
    """
    Создание JWT токена с включением роли
    Принимает роль как UserRole enum ИЛИ как строку ('guest'/'user'/'admin')
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    #enum или строка
    if isinstance(role, UserRole):
        role_value = role.value
    else:
        role_value = str(role)  # Уже строка
    
    to_encode.update({
        "exp": expire,
        "role": role_value
    })
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> dict | None:
    """Верификация токена с возвратом student_id и role"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        student_id: str = payload.get("sub")
        role: str = payload.get("role", UserRole.USER.value)
        if student_id is None:
            return None
        return {"student_id": student_id, "role": role}
    except JWTError:
        return None