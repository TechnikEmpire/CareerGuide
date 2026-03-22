"""Run the canonical dense-only local evaluation workflow."""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys

from backend.app.config import settings
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
            "Run the canonical local dense-only evaluation workflow: "
            "dense tuning, answer export, and answer-evidence scoring."
        )
    )
    parser.add_argument(
        "--dense-output",
        type=Path,
        default=REPO_ROOT / "eval" / "out" / "dense_retrieval_tuning.json",
        help="Output path for dense-only tuning results.",
    )
    parser.add_argument(
        "--answer-output",
        type=Path,
        default=REPO_ROOT / "eval" / "out" / "answer_predictions.json",
        help="Output path for generated answer predictions.",
    )
    parser.add_argument(
        "--answer-score-output",
        type=Path,
        default=REPO_ROOT / "eval" / "out" / "answer_scores.json",
        help="Output path for scored answer-evidence results.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=settings.default_top_k,
        help="Top-k value to use for answer export.",
    )
    parser.add_argument(
        "--candidate-pool",
        type=int,
        default=settings.retrieval_candidate_pool_size,
        help=(
            "Dense candidate pool size to use for answer export. "
            "Ignored by the active dense-only path while reranking remains disabled."
        ),
    )
    parser.add_argument(
        "--allow-online",
        action="store_true",
        help="Allow Hugging Face network access instead of forcing offline local-file behavior.",
    )
    generator_group = parser.add_mutually_exclusive_group()
    generator_group.add_argument(
        "--start-generator-server",
        action="store_true",
        dest="start_generator_server",
        help="Start and stop the local generation server automatically for this workflow.",
    )
    generator_group.add_argument(
        "--no-start-generator-server",
        action="store_false",
        dest="start_generator_server",
        help="Require an already-running local generation server instead of starting one.",
    )
    parser.add_argument(
        "--generator-startup-timeout",
        type=float,
        default=120.0,
        help="Seconds to wait for the local generation server to become ready when auto-starting it.",
    )
    parser.set_defaults(start_generator_server=True)
    return parser.parse_args()


def _run(command: list[str], env: dict[str, str]) -> None:
    print("$ " + " ".join(command))
    subprocess.run(command, check=True, env=env, cwd=REPO_ROOT)


def _ensure_retrieval_artifacts(env: dict[str, str]) -> None:
    from backend.app.services.retrieval.faiss_hnsw import inspect_retrieval_artifacts

    artifact_status = inspect_retrieval_artifacts()
    if artifact_status.sqlite_current and artifact_status.faiss_current:
        return

    print("Refreshing retrieval artifacts before local evaluation.")
    _run([sys.executable, "-m", "backend.scripts.build_retrieval_index"], env)


def main() -> None:
    args = parse_args()
    ensure_local_env_exists(allow_online=args.allow_online)
    env = build_local_env(allow_online=args.allow_online)

    generation_process: subprocess.Popen[bytes] | None = None
    try:
        _ensure_retrieval_artifacts(env)

        if args.start_generator_server:
            base_url = generation_base_url(env)
            if generation_server_ready(base_url):
                print(f"Reusing already-running generation server at: {base_url}")
            else:
                generation_process = subprocess.Popen(
                    [sys.executable, "-m", "backend.scripts.run_local_generation_server"]
                    + (["--allow-online"] if args.allow_online else []),
                    cwd=REPO_ROOT,
                    env=env,
                )
                wait_for_generation_server(
                    base_url=base_url,
                    timeout_seconds=args.generator_startup_timeout,
                    generation_process=generation_process,
                )

        _run(
            [
                sys.executable,
                "-m",
                "backend.scripts.tune_dense_retrieval",
                "--output-json",
                str(args.dense_output),
            ],
            env,
        )
        _run(
            [
                sys.executable,
                "-m",
                "backend.scripts.export_answer_predictions",
                "--top-k",
                str(args.top_k),
                "--candidate-pool",
                str(args.candidate_pool),
                "--output-json",
                str(args.answer_output),
            ],
            env,
        )
        _run(
            [
                sys.executable,
                "-m",
                "eval.score_eval",
                "--answer-predictions",
                str(args.answer_output),
                "--output-json",
                str(args.answer_score_output),
            ],
            env,
        )
    finally:
        terminate_process(generation_process, name="local generation server")


if __name__ == "__main__":
    main()
