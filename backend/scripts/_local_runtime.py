"""Helpers for repo-local model runtime orchestration."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import time

import httpx

REPO_ROOT = Path(__file__).resolve().parents[2]
ENV_LOCAL_PATH = REPO_ROOT / ".env.local"
GENERATOR_CONFIG_PATH = REPO_ROOT / "config" / "llama_cpp_python_server.local.json"
DEFAULT_GENERATION_BASE_URL = "http://127.0.0.1:8080"


def load_env_local() -> dict[str, str]:
    """Parse `.env.local` into a simple key/value mapping."""

    if not ENV_LOCAL_PATH.exists():
        return {}

    values: dict[str, str] = {}
    for line in ENV_LOCAL_PATH.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def build_local_env(*, allow_online: bool) -> dict[str, str]:
    """Build child-process environment using repo-local overrides."""

    env = os.environ.copy()
    for key, value in load_env_local().items():
        env.setdefault(key, value)
    if not allow_online:
        env.setdefault("HF_HUB_OFFLINE", "1")
        env.setdefault("TRANSFORMERS_OFFLINE", "1")
    return env


def ensure_local_env_exists(*, allow_online: bool) -> None:
    """Fail fast when the expected repo-local setup file is missing."""

    if not allow_online and not ENV_LOCAL_PATH.exists():
        raise SystemExit(
            f"Missing local runtime environment file: {ENV_LOCAL_PATH}\n"
            "Run `python -m backend.scripts.setup_local_models` first."
        )


def generation_base_url(env: dict[str, str]) -> str:
    """Return the configured generation base URL from child-process env."""

    return env.get("CAREERGUIDE_GENERATION_BASE_URL", DEFAULT_GENERATION_BASE_URL).rstrip("/")


def wait_for_generation_server(
    *,
    base_url: str,
    timeout_seconds: float,
    generation_process: subprocess.Popen[bytes] | None = None,
) -> None:
    """Poll the OpenAI-compatible model endpoint until it becomes ready."""

    deadline = time.monotonic() + timeout_seconds
    last_error: str | None = None
    endpoint = f"{base_url}/v1/models"

    while time.monotonic() < deadline:
        if generation_process is not None and generation_process.poll() is not None:
            raise SystemExit(
                "The local generation server exited before it became ready. "
                "Check the server output above."
            )
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(endpoint)
                if response.status_code == 200:
                    return
                last_error = f"HTTP {response.status_code}"
        except httpx.HTTPError as exc:
            last_error = str(exc)
        time.sleep(0.5)

    raise SystemExit(
        f"Timed out waiting for the local generation server at {endpoint}.\n"
        f"Last observed error: {last_error or 'no response'}"
    )


def generation_server_ready(base_url: str) -> bool:
    """Return whether the generation server already answers at `/v1/models`."""

    try:
        with httpx.Client(timeout=3.0) as client:
            response = client.get(f"{base_url}/v1/models")
            return response.status_code == 200
    except httpx.HTTPError:
        return False


def terminate_process(process: subprocess.Popen[bytes] | None, *, name: str) -> None:
    """Terminate a child process cleanly, then force-kill if needed."""

    if process is None or process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)
