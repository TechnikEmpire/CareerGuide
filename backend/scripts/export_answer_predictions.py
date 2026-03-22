"""Export generated answers and cited evidence for tracked answer-eval cases."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
import os
from pathlib import Path

from backend.app.config import settings
from backend.app.services.assistant_service import answer_question
from backend.app.services.generation.schemas import AnswerRequest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Export generated answers for the tracked answer-evaluation cases "
            "using the active retrieval and generation configuration."
        )
    )
    parser.add_argument(
        "--answer-cases",
        type=Path,
        default=Path("eval/answer_eval_cases.json"),
        help="Path to the canonical answer-evaluation cases JSON file.",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("eval/out/answer_predictions.json"),
        help="Output path for generated answer predictions.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=settings.default_top_k,
        help="Dense top-k to use when building retrieval context for answers.",
    )
    parser.add_argument(
        "--candidate-pool",
        type=int,
        default=settings.retrieval_candidate_pool_size,
        help=(
            "Dense candidate pool size to use before top-k trimming. "
            "Ignored by the active dense-only path while reranking remains disabled."
        ),
    )
    parser.add_argument(
        "--user-id",
        type=str,
        default="eval-user",
        help="Synthetic user identifier for answer-evaluation exports.",
    )
    device_group = parser.add_mutually_exclusive_group()
    device_group.add_argument(
        "--cpu-only",
        action="store_true",
        dest="cpu_only",
        help="Force CPU-only retrieval-side embedding. This is the default behavior.",
    )
    device_group.add_argument(
        "--allow-gpu",
        action="store_false",
        dest="cpu_only",
        help="Allow CUDA for retrieval-side embedding during export.",
    )
    parser.set_defaults(cpu_only=True)
    return parser.parse_args()


def _load_cases(path: Path) -> list[dict[str, object]]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    args = parse_args()
    if args.cpu_only:
        os.environ["CUDA_VISIBLE_DEVICES"] = ""

    from backend.app.services.generation.generator_client import get_generator_client
    from backend.app.services.retrieval.faiss_hnsw import inspect_retrieval_artifacts

    previous_candidate_pool = settings.retrieval_candidate_pool_size
    settings.retrieval_candidate_pool_size = args.candidate_pool
    get_generator_client.cache_clear()

    try:
        artifact_status = inspect_retrieval_artifacts()
        if not artifact_status.sqlite_current or not artifact_status.faiss_current:
            raise RuntimeError(
                "Retrieval artifacts are missing or stale. "
                "Run `python -m backend.scripts.build_retrieval_index` before exporting answer predictions, "
                "or use `python -m backend.scripts.run_local_eval_workflow`, which now repairs stale "
                "retrieval artifacts automatically."
            )

        answer_cases = _load_cases(args.answer_cases)
        predictions: list[dict[str, object]] = []
        for case in answer_cases:
            request = AnswerRequest(
                user_id=args.user_id,
                question=str(case["question"]),
            )
            response = answer_question(
                request,
                top_k=args.top_k,
                use_reranker=False,
                include_memory=False,
            )
            predictions.append(
                {
                    "case_id": case["id"],
                    "language": case.get("language"),
                    "question": case["question"],
                    "answer_text": response.answer,
                    "prompt_preview": response.prompt_preview,
                    "memory_summary": response.memory_summary,
                    "cited_chunk_ids": [chunk.chunk_id for chunk in response.citations if chunk.chunk_id],
                    "cited_titles": [chunk.title for chunk in response.citations],
                }
            )

        output_payload = {
            "exported_at": datetime.now(UTC).isoformat(),
            "answer_cases_file": str(args.answer_cases),
            "retrieval_artifacts": {
                "chunk_count": artifact_status.chunk_count,
                "embedding_model": artifact_status.embedding_model,
                "vector_size": artifact_status.vector_size,
                "index_path": str(artifact_status.index_path),
                "manifest_path": str(artifact_status.manifest_path),
                "sqlite_current": artifact_status.sqlite_current,
                "faiss_current": artifact_status.faiss_current,
            },
            "generation": {
                "runtime": settings.generation_runtime,
                "model_name": settings.generation_model_name,
                "model_artifact": settings.generation_model_artifact,
                "base_url": settings.generation_base_url,
                "temperature": settings.generation_temperature,
                "top_p": settings.generation_top_p,
                "answer_max_tokens": settings.generation_answer_max_tokens,
            },
            "settings": {
                "top_k": args.top_k,
                "candidate_pool": args.candidate_pool,
                "cpu_only": args.cpu_only,
                "use_reranker": False,
            },
            "predictions": predictions,
        }

        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(
            json.dumps(output_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"Wrote {len(predictions)} answer predictions to: {args.output_json}")
    finally:
        settings.retrieval_candidate_pool_size = previous_candidate_pool
        get_generator_client.cache_clear()


if __name__ == "__main__":
    main()
