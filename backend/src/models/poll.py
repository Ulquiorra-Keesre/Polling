from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from src.database.connection import Base
from typing import Optional


class Poll(Base):
    __tablename__ = "polls"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    total_votes = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    banner_file_id = Column(Integer, ForeignKey("files.id"), nullable=True)
    banner = relationship("FileMetadata", foreign_keys=[banner_file_id], lazy="select")

    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    options = relationship(
        "Option", back_populates="poll", cascade="all, delete-orphan"
    )
    votes = relationship("Vote", back_populates="poll")


class Option(Base):
    __tablename__ = "options"

    id = Column(Integer, primary_key=True, index=True)
    poll_id = Column(Integer, ForeignKey("polls.id", ondelete="CASCADE"))
    text = Column(String, nullable=False)
    votes = Column(Integer, default=0)

    poll = relationship("Poll", back_populates="options")
    votes_entries = relationship("Vote", back_populates="option")


from pydantic import BaseModel, ConfigDict
from typing import List
from datetime import datetime


class OptionBase(BaseModel):
    text: str


class OptionCreate(OptionBase):
    pass


class OptionResponse(OptionBase):
    id: int
    poll_id: int
    votes: int = 0
    percentage: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class PollBase(BaseModel):
    title: str
    description: str
    end_date: datetime


class PollCreate(PollBase):
    options: List[OptionCreate]


class PollResponse(PollBase):
    id: int
    total_votes: int = 0
    options: List[OptionResponse] = []
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PollResults(PollResponse):
    pass
