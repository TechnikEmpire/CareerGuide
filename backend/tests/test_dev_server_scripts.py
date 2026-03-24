"""Tests for local dev-server script helpers."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import PurePath

from backend.scripts.run_backend_dev_server import build_uvicorn_command, ensure_retrieval_artifacts


@dataclass(frozen=True)
class _ArtifactStatus:
    sqlite_current: bool
    faiss_current: bool


def test_build_uvicorn_command_uses_relative_reload_patterns() -> None:
    """Reload glob patterns must remain relative for Uvicorn."""

    args = argparse.Namespace(
        host="127.0.0.1",
        port=8000,
        reload=True,
        allow_online=False,
    )

    command = build_uvicorn_command(args)

    exclude_values = [
        command[index + 1]
        for index, token in enumerate(command)
        if token == "--reload-exclude"
    ]
    reload_dirs = [
        command[index + 1]
        for index, token in enumerate(command)
        if token == "--reload-dir"
    ]

    assert exclude_values
    assert reload_dirs == ["backend"]
    assert all(not PurePath(pattern).is_absolute() for pattern in exclude_values)
    assert all(not PurePath(directory).is_absolute() for directory in reload_dirs)


def test_ensure_retrieval_artifacts_skips_rebuild_when_artifacts_are_current() -> None:
    calls: list[list[str]] = []

    ensure_retrieval_artifacts(
        {"HF_HUB_OFFLINE": "1"},
        inspect_status=lambda: _ArtifactStatus(sqlite_current=True, faiss_current=True),
        run_command=lambda command, **kwargs: calls.append(command),
    )

    assert calls == []


def test_ensure_retrieval_artifacts_rebuilds_when_artifacts_are_stale() -> None:
    calls: list[tuple[list[str], dict[str, object]]] = []

    def fake_run(command: list[str], **kwargs: object) -> None:
        calls.append((command, kwargs))

    env = {"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"}
    ensure_retrieval_artifacts(
        env,
        inspect_status=lambda: _ArtifactStatus(sqlite_current=False, faiss_current=True),
        run_command=fake_run,
    )

    assert len(calls) == 1
    command, kwargs = calls[0]
    assert command[1:] == ["-m", "backend.scripts.build_retrieval_index"]
    assert kwargs["check"] is True
    assert kwargs["env"] == env
