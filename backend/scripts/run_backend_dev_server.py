"""Run the local FastAPI development server with repo-local settings."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]


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
        command.extend(
            [
                "--reload",
                "--reload-dir",
                str(REPO_ROOT / "backend"),
                "--reload-exclude",
                str(REPO_ROOT / "data" / "processed" / "*"),
                "--reload-exclude",
                str(REPO_ROOT / "models" / "*"),
                "--reload-exclude",
                str(REPO_ROOT / "eval" / "out" / "*"),
                "--reload-exclude",
                str(REPO_ROOT / "config" / "*.local.json"),
                "--reload-exclude",
                str(REPO_ROOT / ".env.local"),
            ]
        )
    os.execvpe(command[0], command, env)


if __name__ == "__main__":
    main()
