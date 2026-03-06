# backend/src/utils/security.py
from datetime import datetime, timedelta
from jose import JWTError, jwt
from src.config import settings
from src.models.user import UserRole
import hashlib

ACCESS_TOKEN_EXPIRE_MINUTES = 15  # минут
REFRESH_TOKEN_EXPIRE_DAYS = 3     # дней

def create_access_token(data: dict, role: UserRole | str = UserRole.USER):
    """Создание access токена (короткое время жизни)"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    if isinstance(role, UserRole):
        role_value = role.value
    else:
        role_value = str(role)
    
    to_encode.update({
        "exp": expire,
        "role": role_value,
        "type": "access"
    })
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(student_id: str) -> tuple[str, datetime]:
    """
    Создание refresh токена (длительное время жизни)
    Возвращает: (token, expires_at)
    """
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode = {
        "sub": student_id,
        "exp": expire,
        "type": "refresh",
        "jti": hashlib.sha256(f"{student_id}{datetime.utcnow().isoformat()}".encode()).hexdigest()[:16]
    }
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt, expire

def verify_token(token: str, expected_type: str = "access") -> dict | None:
    """
    Верификация токена с проверкой типа
    expected_type: "access" или "refresh"
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        token_type = payload.get("type")
        if token_type != expected_type:
            return None
        
        student_id: str = payload.get("sub")
        role: str = payload.get("role", UserRole.USER.value)
        
        if student_id is None:
            return None
        
        return {
            "student_id": student_id,
            "role": role,
            "exp": payload.get("exp"),
            "jti": payload.get("jti")
        }
    except JWTError:
        return None

def hash_token(token: str) -> str:
    """Хэширование токена для безопасного хранения в БД"""
    return hashlib.sha256(token.encode()).hexdigest()