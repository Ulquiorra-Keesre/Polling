from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from src.database.connection import Base

class Vote(Base):
    __tablename__ = "votes"

    id = Column(Integer, primary_key=True, index=True)
    
    poll_id = Column(Integer, ForeignKey("polls.id", ondelete="CASCADE"), nullable=False)
    option_id = Column(Integer, ForeignKey("options.id", ondelete="CASCADE"), nullable=False)
    
    student_id = Column(String, ForeignKey("users.student_id", ondelete="CASCADE"), nullable=False)
    
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="votes")

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