"""Run the full local app stack with one command."""

from __future__ import annotations

import argparse
import subprocess
import sys
import time

from backend.scripts._local_runtime import (
    REPO_ROOT,
    build_local_env,
    ensure_local_env_exists,
    generation_base_url,
    generation_server_ready,
    terminate_process,
    wait_for_generation_server,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Start the local generation server and the FastAPI backend together "
            "as a single local app-stack command."
        )
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host for the backend app server.")
    parser.add_argument("--port", type=int, default=8000, help="Port for the backend app server.")
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable Uvicorn reload mode for backend development.",
    )
    parser.add_argument(
        "--allow-online",
        action="store_true",
        help="Allow Hugging Face network access instead of forcing offline local-file behavior.",
    )
    parser.add_argument(
        "--generator-startup-timeout",
        type=float,
        default=120.0,
        help="Seconds to wait for the local generation server to become ready.",
    )
    return parser.parse_args()


def _spawn(command: list[str], env: dict[str, str]) -> subprocess.Popen[bytes]:
    return subprocess.Popen(command, cwd=REPO_ROOT, env=env)


def main() -> None:
    args = parse_args()
    ensure_local_env_exists(allow_online=args.allow_online)
    env = build_local_env(allow_online=args.allow_online)
    base_url = generation_base_url(env)

    generator_process: subprocess.Popen[bytes] | None = None
    backend_process: subprocess.Popen[bytes] | None = None

    try:
        if generation_server_ready(base_url):
            print(f"Reusing already-running generation server at: {base_url}")
        else:
            generator_process = _spawn(
                [sys.executable, "-m", "backend.scripts.run_local_generation_server"]
                + (["--allow-online"] if args.allow_online else []),
                env,
            )
            wait_for_generation_server(
                base_url=base_url,
                timeout_seconds=args.generator_startup_timeout,
                generation_process=generator_process,
            )
        backend_process = _spawn(
            [
                sys.executable,
                "-m",
                "backend.scripts.run_backend_dev_server",
                "--host",
                args.host,
                "--port",
                str(args.port),
            ]
            + (["--reload"] if args.reload else [])
            + (["--allow-online"] if args.allow_online else []),
            env,
        )
        print(f"Local generation server ready at: {base_url}")
        print(f"Local backend app ready at: http://{args.host}:{args.port}")
        print("Press Ctrl+C to stop both processes.")

        while True:
            if generator_process.poll() is not None:
                raise SystemExit("The local generation server exited unexpectedly.")
            if backend_process.poll() is not None:
                raise SystemExit("The backend app server exited unexpectedly.")
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        terminate_process(backend_process, name="backend app server")
        terminate_process(generator_process, name="local generation server")


if __name__ == "__main__":
    main()
