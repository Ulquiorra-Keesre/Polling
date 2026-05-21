# src/models/vote.py
"""SQLAlchemy модель для голосования"""

from typing import TYPE_CHECKING
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from src.database.connection import Base

# 🔹 Для типизации циклических импортов (mypy/ruff)
if TYPE_CHECKING:
    from src.models.poll import Poll, Option
    from src.models.user import User


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

    # 🔹 Связи
    poll: "Poll" = relationship("Poll", back_populates="votes")
    option: "Option" = relationship("Option", back_populates="votes_entries")
    user: "User" = relationship("User", back_populates="votes")

    __table_args__ = (
        UniqueConstraint("poll_id", "student_id", name="uq_vote_poll_student"),
    )
