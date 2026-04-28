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


def _default_retrieval_index_path() -> Path:
    return _repo_root() / "data" / "processed" / "retrieval" / "faiss_hnsw.index"


def _default_retrieval_manifest_path() -> Path:
    return _repo_root() / "data" / "processed" / "retrieval" / "faiss_hnsw_manifest.json"


def _default_memory_extraction_model_path() -> Path:
    return (
        _repo_root()
        / "tooling"
        / "memory_extraction"
        / "models"
        / "bilstm_memory_classifier_binary.pt"
    )


def _default_frontend_dev_origins() -> list[str]:
    return [
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://localhost:3000",
    ]


def _default_frontend_dist_path() -> Path:
    return _repo_root() / "frontend" / "dist"


class AppSettings(BaseSettings):
    """Environment-driven backend settings."""

    app_name: str = "CareerGuide API"
    app_env: str = "development"
    debug: bool = True
    database_url: str = Field(default_factory=_default_database_url)
    frontend_dev_origins: list[str] = Field(default_factory=_default_frontend_dev_origins)
    frontend_dist_path: Path = Field(default_factory=_default_frontend_dist_path)
    serve_frontend: bool = True
    default_top_k: int = 10
    memory_vector_size: int = 32
    memory_extraction_backend: str = "bilstm"
    memory_extraction_sentence_splitter: str = "pysbd"
    memory_extraction_model_path: Path = Field(default_factory=_default_memory_extraction_model_path)
    memory_extraction_device: str = "cpu"
    memory_extraction_min_confidence: float = 0.75
    memory_extraction_min_segment_characters: int = 10
    memory_extraction_default_category: str = "user_memory"
    memory_extraction_default_importance: float = 0.7
    memory_hopfield_mode: str = "topk"
    memory_hopfield_top_k: int = 3
    memory_hopfield_beta: float = 8.0
    esco_concepts_path: Path = Field(default_factory=_default_esco_concepts_path)
    esco_relations_path: Path = Field(default_factory=_default_esco_relations_path)
    esco_bilingual_concepts_path: Path = Field(default_factory=_default_esco_bilingual_path)
    esco_skill_limit_per_occupation: int = 8
    generation_runtime: str = "llama-cpp-python"
    generation_model_name: str = "Qwen/Qwen3.5-2B"
    generation_model_artifact: str = "bartowski/Qwen_Qwen3.5-2B-GGUF:Q4_K_M"
    generation_base_url: str = "http://127.0.0.1:8080"
    generation_request_timeout_seconds: float = 180.0
    generation_temperature: float = 0.2
    generation_top_p: float = 0.9
    generation_answer_max_tokens: int = 512
    generation_plan_max_tokens: int = 768
    generation_skill_enrichment_max_tokens: int = 384
    generation_context_length: int = 8192
    retrieval_index_path: Path = Field(default_factory=_default_retrieval_index_path)
    retrieval_index_manifest_path: Path = Field(default_factory=_default_retrieval_manifest_path)
    retrieval_vector_size: int = 1024
    retrieval_embedding_provider: str = "qwen3"
    retrieval_embedding_model_id: str = "Qwen/Qwen3-Embedding-0.6B"
    retrieval_embedding_model_name: str = "Qwen/Qwen3-Embedding-0.6B"
    retrieval_query_instruction: str = (
        "Given a career guidance question, retrieve passages that best answer the question."
    )
    retrieval_enable_reranker: bool = False
    retrieval_reranker_provider: str = "qwen3"
    retrieval_reranker_model_id: str = "Qwen/Qwen3-Reranker-0.6B"
    retrieval_reranker_model_name: str = "Qwen/Qwen3-Reranker-0.6B"
    retrieval_embedding_batch_size: int = 32
    retrieval_reranker_batch_size: int = 8
    retrieval_reranker_max_length: int = 2048
    retrieval_candidate_pool_size: int = 10
    faiss_hnsw_m: int = 32
    faiss_hnsw_ef_construction: int = 80
    faiss_hnsw_ef_search: int = 64

    model_config = SettingsConfigDict(
        env_prefix="CAREERGUIDE_",
        env_file=(".env", ".env.local"),
        extra="ignore",
    )


settings = AppSettings()
