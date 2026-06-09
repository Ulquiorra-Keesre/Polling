from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, Mapped

from src.database.connection import Base
from typing import List
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from src.models.vote import Vote
    from src.models.file import FileMetadata


class Poll(Base):
    """Модель опроса"""

    __tablename__ = "polls"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    total_votes = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    banner_file_id = Column(Integer, ForeignKey("files.id"), nullable=True)
    banner: Mapped[Optional["FileMetadata"]] = relationship(
        "FileMetadata",
        foreign_keys=[banner_file_id],
        lazy="select",
        back_populates="polls_as_banner",
    )

    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    options: Mapped[list["Option"]] = relationship(
        "Option", back_populates="poll", cascade="all, delete-orphan", lazy="select"
    )
    votes: Mapped[list["Vote"]] = relationship("Vote", back_populates="poll", lazy="select")


class Option(Base):
    """Модель варианта ответа"""

    __tablename__ = "options"

    id = Column(Integer, primary_key=True, index=True)
    poll_id = Column(
        Integer, ForeignKey("polls.id", ondelete="CASCADE"), nullable=False
    )
    text = Column(String, nullable=False)
    votes = Column(Integer, default=0)

    poll: Mapped["Poll"] = relationship("Poll", back_populates="options")
    votes_entries: Mapped[list["Vote"]] = relationship(
        "Vote", back_populates="option", lazy="select"
    )
