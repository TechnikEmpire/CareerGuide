"""Runtime settings for the CareerGuide backend."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_database_url() -> str:
    """Build a SQLite path inside the repository.

    Keeping the default database inside `data/processed` makes the demo easy to
    inspect and avoids scattering local state around a developer machine.
    """

    repo_root = Path(__file__).resolve().parents[2]
    database_path = repo_root / "data" / "processed" / "careerguide.db"
    return f"sqlite:///{database_path}"


class AppSettings(BaseSettings):
    """Environment-driven backend settings."""

    app_name: str = "CareerGuide API"
    app_env: str = "development"
    debug: bool = True
    database_url: str = Field(default_factory=_default_database_url)
    default_top_k: int = 5
    memory_vector_size: int = 32

    model_config = SettingsConfigDict(
        env_prefix="CAREERGUIDE_",
        env_file=".env",
        extra="ignore",
    )


settings = AppSettings()
