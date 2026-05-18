"""Модели и схемы для голосования"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from src.database.connection import Base


class Vote(Base):
    """Таблица голосов в БД"""

    __tablename__ = "votes"

    id = Column(Integer, primary_key=True, index=True)

    poll_id = Column(
        Integer, ForeignKey("polls.id", ondelete="CASCADE"), nullable=False
    )
    option_id = Column(
        Integer, ForeignKey("options.id", ondelete="CASCADE"), nullable=False
    )

    student_id = Column(
        String, ForeignKey("users.student_id", ondelete="CASCADE"), nullable=False
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    poll = relationship("Poll", back_populates="votes")
    option = relationship("Option", back_populates="votes_entries")
    user = relationship("User", back_populates="votes")

    __table_args__ = (
        UniqueConstraint("poll_id", "student_id", name="uq_vote_poll_student"),
    )


from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional


class VoteCreate(BaseModel):
    """
    Схема для создания голоса.

    🔹 ВАЖНО: student_id НЕ включён сюда!
    Он извлекается из токена авторизации в маршруте.
    """

    poll_id: int = Field(..., gt=0, description="ID опроса")
    option_id: int = Field(..., gt=0, description="ID варианта ответа")


class VoteResponse(BaseModel):
    """Схема ответа с данными о голосе"""

    id: int
    poll_id: int
    option_id: int
    student_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VoteCheckResponse(BaseModel):
    """Ответ на проверку: голосовал ли пользователь"""

    poll_id: int
    student_id: str
    has_voted: bool
    voted_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UserVotesResponse(BaseModel):
    """Ответ со списком голосов пользователя"""

    student_id: str
    votes: list[VoteResponse]
    total: int = 0

    model_config = ConfigDict(from_attributes=True)
