"""Download repo-local model artifacts and generate local runtime config."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from huggingface_hub import snapshot_download

REPO_ROOT = Path(__file__).resolve().parents[2]
MODELS_DIR = REPO_ROOT / "models"
CONFIG_DIR = REPO_ROOT / "config"
ENV_LOCAL_PATH = REPO_ROOT / ".env.local"

GENERATOR_REPO_ID = "ggml-org/Qwen3-0.6B-GGUF"
GENERATOR_ALLOW_PATTERNS = ["*Q8_0.gguf"]
EMBEDDING_REPO_ID = "Qwen/Qwen3-Embedding-0.6B"
RERANKER_REPO_ID = "Qwen/Qwen3-Reranker-0.6B"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Download the local generator and retrieval models into the repo, "
            "create .env.local, and create the local llama_cpp.server config."
        )
    )
    parser.add_argument(
        "--include-reranker",
        action="store_true",
        help="Also download the reranker model locally, even though it is disabled by default.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force-refresh the local config and environment files.",
    )
    return parser.parse_args()


def _download_snapshot(*, repo_id: str, local_dir: Path, allow_patterns: list[str] | None = None) -> Path:
    local_dir.mkdir(parents=True, exist_ok=True)
    snapshot_download(
        repo_id=repo_id,
        local_dir=str(local_dir),
        allow_patterns=allow_patterns,
    )
    return local_dir


def _find_single_file(root: Path, pattern: str) -> Path:
    matches = sorted(root.rglob(pattern))
    if not matches:
        raise FileNotFoundError(f"Could not find a file matching {pattern!r} under {root}.")
    if len(matches) > 1:
        raise RuntimeError(
            f"Expected one file matching {pattern!r} under {root}, but found {len(matches)}."
        )
    return matches[0].resolve()


def _write_env_local(
    *,
    embedding_dir: Path,
    reranker_dir: Path | None,
    force: bool,
) -> None:
    if ENV_LOCAL_PATH.exists() and not force:
        existing_lines = ENV_LOCAL_PATH.read_text(encoding="utf-8").splitlines()
        filtered = [
            line for line in existing_lines
            if not line.startswith("CAREERGUIDE_RETRIEVAL_EMBEDDING_MODEL_NAME=")
            and not line.startswith("CAREERGUIDE_RETRIEVAL_EMBEDDING_MODEL_ID=")
            and not line.startswith("CAREERGUIDE_RETRIEVAL_RERANKER_MODEL_NAME=")
            and not line.startswith("CAREERGUIDE_RETRIEVAL_RERANKER_MODEL_ID=")
            and not line.startswith("CAREERGUIDE_GENERATION_RUNTIME=")
            and not line.startswith("CAREERGUIDE_GENERATION_BASE_URL=")
            and not line.startswith("CAREERGUIDE_RETRIEVAL_ENABLE_RERANKER=")
        ]
    else:
        filtered = []

    filtered.extend(
        [
            f"CAREERGUIDE_RETRIEVAL_EMBEDDING_MODEL_ID={EMBEDDING_REPO_ID}",
            f"CAREERGUIDE_RETRIEVAL_EMBEDDING_MODEL_NAME={embedding_dir.resolve()}",
            "CAREERGUIDE_GENERATION_RUNTIME=llama-cpp-python",
            "CAREERGUIDE_GENERATION_BASE_URL=http://127.0.0.1:8080",
            "CAREERGUIDE_RETRIEVAL_ENABLE_RERANKER=false",
        ]
    )
    if reranker_dir is not None:
        filtered.append(f"CAREERGUIDE_RETRIEVAL_RERANKER_MODEL_ID={RERANKER_REPO_ID}")
        filtered.append(f"CAREERGUIDE_RETRIEVAL_RERANKER_MODEL_NAME={reranker_dir.resolve()}")

    ENV_LOCAL_PATH.write_text("\n".join(filtered).rstrip() + "\n", encoding="utf-8")


def _write_server_config(*, gguf_path: Path) -> Path:
    example_path = CONFIG_DIR / "llama_cpp_python_server.example.json"
    local_config_path = CONFIG_DIR / "llama_cpp_python_server.local.json"
    payload = json.loads(example_path.read_text(encoding="utf-8"))
    payload["models"][0]["model"] = str(gguf_path.resolve())
    local_config_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return local_config_path


def main() -> None:
    args = parse_args()
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    generator_dir = _download_snapshot(
        repo_id=GENERATOR_REPO_ID,
        local_dir=MODELS_DIR / "Qwen3-0.6B-GGUF",
        allow_patterns=GENERATOR_ALLOW_PATTERNS,
    )
    embedding_dir = _download_snapshot(
        repo_id=EMBEDDING_REPO_ID,
        local_dir=MODELS_DIR / "Qwen3-Embedding-0.6B",
    )
    reranker_dir = None
    if args.include_reranker:
        reranker_dir = _download_snapshot(
            repo_id=RERANKER_REPO_ID,
            local_dir=MODELS_DIR / "Qwen3-Reranker-0.6B",
        )

    gguf_path = _find_single_file(generator_dir, "*Q8_0.gguf")
    local_config_path = _write_server_config(gguf_path=gguf_path)
    _write_env_local(
        embedding_dir=embedding_dir,
        reranker_dir=reranker_dir,
        force=args.force,
    )

    print(f"Downloaded generator artifacts to: {generator_dir}")
    print(f"Resolved GGUF file: {gguf_path}")
    print(f"Downloaded embedding model to: {embedding_dir}")
    if reranker_dir is not None:
        print(f"Downloaded reranker model to: {reranker_dir}")
    print(f"Wrote local runtime config: {local_config_path}")
    print(f"Wrote local environment overrides: {ENV_LOCAL_PATH}")


if __name__ == "__main__":
    main()
