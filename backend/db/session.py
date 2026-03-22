"""Database engine and session helpers."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.app.config import settings
from backend.db.models import Base


database_path = Path(settings.database_url.removeprefix("sqlite:///"))
database_path.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)


def init_db() -> None:
    """Initialize database tables for the local MVP."""

    Base.metadata.create_all(bind=engine)


def get_session() -> Session:
    """Yield a database session.

    We keep this as a simple function for now. It can later become a FastAPI
    dependency provider once real persistence is wired into the API layer.
    """

    return SessionLocal()
