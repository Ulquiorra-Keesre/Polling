from sqlalchemy import Column, Integer, String, DateTime, BigInteger, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, Mapped
from src.database.connection import Base
from src.models.user import User
from src.models.poll import Poll
from typing import Optional


class FileMetadata(Base):
    """Метаданные загруженных файлов"""

    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)

    entity_type = Column(String, nullable=False)
    entity_id = Column(Integer, nullable=False)
    category = Column(String, nullable=False)

    file_key = Column(String, unique=True, nullable=False)
    original_filename = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    size_bytes = Column(BigInteger, nullable=False)

    uploaded_by = Column(String, ForeignKey("users.student_id"), nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    uploader: Mapped["User"] = relationship("User", back_populates="uploaded_files")

    polls_as_banner: Mapped[Optional[list["Poll"]]] = relationship(
        "Poll",
        foreign_keys="Poll.banner_file_id",
        back_populates="banner",
        lazy="select",
    )
