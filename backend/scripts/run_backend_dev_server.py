"""Run the local FastAPI development server with repo-local settings."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
RELOAD_DIRS = ("backend",)
RELOAD_EXCLUDES = (
    "data/processed/*",
    "models/*",
    "eval/out/*",
    "config/*.local.json",
    ".env.local",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Start the local FastAPI development server for CareerGuide."
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host address for the backend server.")
    parser.add_argument("--port", type=int, default=8000, help="Port for the backend server.")
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable Uvicorn reload mode for local development.",
    )
    parser.add_argument(
        "--allow-online",
        action="store_true",
        help="Allow Hugging Face network access instead of forcing offline local-file behavior.",
    )
    return parser.parse_args()


def build_uvicorn_command(args: argparse.Namespace) -> list[str]:
    """Build the Uvicorn command for the local backend dev server.

    Uvicorn reload globs must stay relative to the current working directory.
    Absolute patterns crash under pathlib glob handling.
    """

    command = [
        sys.executable,
        "-m",
        "uvicorn",
        "backend.app.main:app",
        "--host",
        args.host,
        "--port",
        str(args.port),
    ]
    if args.reload:
        command.append("--reload")
        for reload_dir in RELOAD_DIRS:
            command.extend(["--reload-dir", reload_dir])
        for pattern in RELOAD_EXCLUDES:
            command.extend(["--reload-exclude", pattern])
    return command


def ensure_retrieval_artifacts(
    env: dict[str, str],
    *,
    inspect_status=None,
    run_command=None,
) -> None:
    """Repair stale retrieval artifacts before starting the backend server."""

    if inspect_status is None:
        from backend.app.services.retrieval.faiss_hnsw import inspect_retrieval_artifacts

        inspect_status = inspect_retrieval_artifacts
    if run_command is None:
        run_command = subprocess.run

    artifact_status = inspect_status()
    if artifact_status.sqlite_current and artifact_status.faiss_current:
        return

    print("Refreshing retrieval artifacts before starting the backend server.")
    run_command(
        [sys.executable, "-m", "backend.scripts.build_retrieval_index"],
        check=True,
        env=env,
        cwd=REPO_ROOT,
    )


def main() -> None:
    args = parse_args()
    env_local_path = REPO_ROOT / ".env.local"
    if not args.allow_online and not env_local_path.exists():
        raise SystemExit(
            f"Missing local runtime environment file: {env_local_path}\n"
            "Run `python -m backend.scripts.setup_local_models` first."
        )

    os.chdir(REPO_ROOT)
    env = os.environ.copy()
    if not args.allow_online:
        env.setdefault("HF_HUB_OFFLINE", "1")
        env.setdefault("TRANSFORMERS_OFFLINE", "1")

    ensure_retrieval_artifacts(env)
    command = build_uvicorn_command(args)
    os.execvpe(command[0], command, env)


if __name__ == "__main__":
    main()
