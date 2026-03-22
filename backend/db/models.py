"""Core SQLAlchemy models for the MVP scaffold."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all ORM models."""


class SourceDocument(Base):
    """Authority-tracked source document."""

    __tablename__ = "source_documents"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    source_name: Mapped[str] = mapped_column(String(100), index=True)
    title: Mapped[str] = mapped_column(String(255))
    url: Mapped[str] = mapped_column(String(500))
    source_type: Mapped[str] = mapped_column(String(50), default="reference")


class Chunk(Base):
    """Chunked text unit used for retrieval."""

    __tablename__ = "chunks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    document_id: Mapped[int | None] = mapped_column(index=True, nullable=True)
    title: Mapped[str] = mapped_column(String(255))
    text: Mapped[str] = mapped_column(Text())
    chunk_type: Mapped[str] = mapped_column(String(50), index=True)
    source_name: Mapped[str] = mapped_column(String(100), index=True)


class MemoryItem(Base):
    """Stored user preference, goal, or constraint."""

    __tablename__ = "memory_items"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    text: Mapped[str] = mapped_column(Text())
    category: Mapped[str] = mapped_column(String(64), index=True)
    importance: Mapped[float] = mapped_column(Float())
    confidence: Mapped[float] = mapped_column(Float())
    created_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow)
