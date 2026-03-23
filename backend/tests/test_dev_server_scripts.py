"""Tests for local dev-server script helpers."""

from __future__ import annotations

import argparse
from pathlib import PurePath

from backend.scripts.run_backend_dev_server import build_uvicorn_command


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
