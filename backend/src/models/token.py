from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from src.database.connection import Base

class RefreshToken(Base):
    """
    Модель для хранения refresh токенов
    Позволяет отслеживать и отзывать сессии
    """
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    
    student_id = Column(String, ForeignKey("users.student_id", ondelete="CASCADE"), nullable=False, index=True)
    
    token_hash = Column(String, nullable=False, unique=True, index=True)
    
    is_revoked = Column(Boolean, default=False, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    
    user = relationship("User", back_populates="refresh_tokens")