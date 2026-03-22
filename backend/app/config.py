"""Runtime settings for the CareerGuide backend."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _repo_root() -> Path:
    """Return the repository root."""

    return Path(__file__).resolve().parents[2]


def _default_database_url() -> str:
    """Build a SQLite path inside the repository.

    Keeping the default database inside `data/processed` makes the demo easy to
    inspect and avoids scattering local state around a developer machine.
    """

    database_path = _repo_root() / "data" / "processed" / "careerguide.db"
    return f"sqlite:///{database_path}"


def _default_esco_concepts_path() -> Path:
    return _repo_root() / "data" / "processed" / "esco" / "normalized" / "esco_concepts.en.jsonl"


def _default_esco_relations_path() -> Path:
    return _repo_root() / "data" / "processed" / "esco" / "normalized" / "esco_relations.jsonl"


def _default_esco_bilingual_path() -> Path:
    return _repo_root() / "data" / "processed" / "esco" / "bilingual" / "esco_concepts.en_ru.jsonl"


class AppSettings(BaseSettings):
    """Environment-driven backend settings."""

    app_name: str = "CareerGuide API"
    app_env: str = "development"
    debug: bool = True
    database_url: str = Field(default_factory=_default_database_url)
    default_top_k: int = 5
    memory_vector_size: int = 32
    esco_concepts_path: Path = Field(default_factory=_default_esco_concepts_path)
    esco_relations_path: Path = Field(default_factory=_default_esco_relations_path)
    esco_bilingual_concepts_path: Path = Field(default_factory=_default_esco_bilingual_path)
    esco_skill_limit_per_occupation: int = 8
    generation_runtime: str = "llama.cpp"
    generation_model_name: str = "Qwen/Qwen3-0.6B"
    generation_model_artifact: str = "Qwen/Qwen3-0.6B-GGUF:Q8_0"
    generation_context_length: int = 32768
    retrieval_vector_size: int = 1024
    retrieval_embedding_provider: str = "qwen3"
    retrieval_embedding_model_name: str = "Qwen/Qwen3-Embedding-0.6B"
    retrieval_query_instruction: str = (
        "Given a career guidance question, retrieve passages that best answer the question."
    )
    retrieval_reranker_provider: str = "qwen3"
    retrieval_reranker_model_name: str = "Qwen/Qwen3-Reranker-0.6B"
    retrieval_embedding_batch_size: int = 32
    retrieval_reranker_batch_size: int = 8
    retrieval_reranker_max_length: int = 2048
    retrieval_candidate_pool_size: int = 20
    faiss_hnsw_m: int = 32
    faiss_hnsw_ef_construction: int = 80
    faiss_hnsw_ef_search: int = 64

    model_config = SettingsConfigDict(
        env_prefix="CAREERGUIDE_",
        env_file=".env",
        extra="ignore",
    )


settings = AppSettings()
