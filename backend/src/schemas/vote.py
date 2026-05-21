# src/schemas/vote.py
"""Pydantic-схемы для голосования (совместимо с Pydantic v2)"""

from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional
from datetime import datetime


class VoteCreate(BaseModel):
    """Схема для создания голоса (student_id берётся из токена)"""

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
    votes: List[VoteResponse] = Field(default_factory=list)
    total: int = 0

    model_config = ConfigDict(from_attributes=True)
