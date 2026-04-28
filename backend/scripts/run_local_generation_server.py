"""Run the local llama_cpp.server process with the generated repo-local config."""

from __future__ import annotations

import argparse
from importlib.metadata import PackageNotFoundError, version
import importlib.util
import json
import os
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
MIN_LLAMA_CPP_PYTHON_VERSION = "0.3.21"


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


def _version_tuple(value: str) -> tuple[int, ...]:
    parts: list[int] = []
    for part in value.split("."):
        number = ""
        for character in part:
            if not character.isdigit():
                break
            number += character
        if number:
            parts.append(int(number))
    return tuple(parts)


def ensure_supported_llama_cpp_python() -> None:
    """Fail early when the bundled llama.cpp backend cannot load Qwen3.5."""

    try:
        installed_version = version("llama-cpp-python")
    except PackageNotFoundError as exc:
        raise SystemExit(
            "Missing `llama-cpp-python[server]` in the active environment.\n"
            "Install it with `python -m pip install -r requirements-runtime.txt`."
        ) from exc

    if _version_tuple(installed_version) < _version_tuple(MIN_LLAMA_CPP_PYTHON_VERSION):
        raise SystemExit(
            "The installed `llama-cpp-python` is too old for Qwen3.5 GGUF files.\n"
            f"Installed: {installed_version}; required: >= {MIN_LLAMA_CPP_PYTHON_VERSION}.\n"
            "Upgrade it with `python -m pip install --upgrade --force-reinstall "
            "-r requirements-runtime.txt`."
        )


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
    ensure_supported_llama_cpp_python()
    if importlib.util.find_spec("llama_cpp.server") is None:
        raise SystemExit("Missing `llama_cpp.server`; reinstall `requirements-runtime.txt`.")

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
