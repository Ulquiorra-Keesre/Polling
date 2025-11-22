# backend/src/models/vote.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from src.database.connection import Base

class Vote(Base):
    __tablename__ = "votes"

    id = Column(Integer, primary_key=True, index=True)
    poll_id = Column(Integer, ForeignKey("polls.id", ondelete="CASCADE"))
    option_id = Column(Integer, ForeignKey("options.id", ondelete="CASCADE"))
    student_id = Column(String, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

# Pydantic модели
from pydantic import BaseModel, ConfigDict
from datetime import datetime

class VoteBase(BaseModel):
    poll_id: int
    option_id: int
    student_id: str

class VoteCreate(VoteBase):
    pass

class VoteResponse(VoteBase):
    id: int
    timestamp: datetime
    
    model_config = ConfigDict(from_attributes=True)