from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from app.database import Base

EMBEDDING_DIM = 384


class Theme(Base):
    __tablename__ = "themes"

    id = Column(Integer, primary_key=True, index=True)
    label = Column(String, nullable=False)
    summary = Column(Text, nullable=True)
    centroid = Column(Vector(EMBEDDING_DIM), nullable=False)
    entry_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    entries = relationship("FeedbackEntry", back_populates="theme")


class FeedbackEntry(Base):
    __tablename__ = "feedback_entries"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    feedback_at = Column(DateTime(timezone=True), nullable=False)
    embedding = Column(Vector(EMBEDDING_DIM), nullable=False)
    theme_id = Column(Integer, ForeignKey("themes.id", ondelete="SET NULL"), nullable=True)
    ingested_at = Column(DateTime(timezone=True), server_default=func.now())

    theme = relationship("Theme", back_populates="entries")