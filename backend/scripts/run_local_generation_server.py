"""Run the local llama_cpp.server process with the generated repo-local config."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Start the local llama_cpp.server process using the repo-local config file."
    )
    parser.add_argument(
        "--config-file",
        type=Path,
        default=REPO_ROOT / "config" / "llama_cpp_python_server.local.json",
        help="Path to the local llama_cpp.server JSON config.",
    )
    parser.add_argument(
        "--allow-online",
        action="store_true",
        help="Allow Hugging Face network access instead of forcing offline local-file behavior.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.config_file.exists():
        raise SystemExit(
            f"Missing local server config: {args.config_file}\n"
            "Run `python -m backend.scripts.setup_local_models` first."
        )

    payload = json.loads(args.config_file.read_text(encoding="utf-8"))
    try:
        configured_model_path = Path(payload["models"][0]["model"])
    except (KeyError, IndexError, TypeError) as exc:
        raise SystemExit(
            f"Invalid local server config: {args.config_file}\n"
            "Run `python -m backend.scripts.setup_local_models --force` to regenerate it."
        ) from exc
    if not configured_model_path.exists():
        raise SystemExit(
            f"Configured GGUF file does not exist: {configured_model_path}\n"
            "Run `python -m backend.scripts.setup_local_models --force` to regenerate the local paths."
        )
    if importlib.util.find_spec("llama_cpp.server") is None:
        raise SystemExit(
            "Missing `llama-cpp-python[server]` in the active environment.\n"
            "Install it with `python -m pip install -r requirements-runtime.txt`."
        )

    os.chdir(REPO_ROOT)
    env = os.environ.copy()
    if not args.allow_online:
        env.setdefault("HF_HUB_OFFLINE", "1")
        env.setdefault("TRANSFORMERS_OFFLINE", "1")

    command = [
        sys.executable,
        "-m",
        "llama_cpp.server",
        "--config_file",
        str(args.config_file),
    ]
    os.execvpe(command[0], command, env)


if __name__ == "__main__":
    main()
