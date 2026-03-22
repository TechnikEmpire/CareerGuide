"""Evaluation inventory helpers for retrieval and answer-quality fixtures."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _eval_dir() -> Path:
    return Path(__file__).resolve().parent


def _load_json_file(filename: str) -> list[dict[str, Any]]:
    path = _eval_dir() / filename
    return json.loads(path.read_text(encoding="utf-8"))


def load_demo_scenarios() -> list[dict[str, Any]]:
    """Load the bilingual demo scenarios used for product-level smoke coverage."""

    return _load_json_file("scenarios.json")


def load_retrieval_queries() -> list[dict[str, Any]]:
    """Load the canonical retrieval benchmark query set."""

    return _load_json_file("retrieval_benchmark_queries.json")


def load_retrieval_qrels() -> list[dict[str, Any]]:
    """Load graded relevance labels for retrieval evaluation."""

    return _load_json_file("retrieval_qrels.json")


def load_answer_eval_cases() -> list[dict[str, Any]]:
    """Load answer-level evaluation cases with expected evidence chunks."""

    return _load_json_file("answer_eval_cases.json")


def build_eval_inventory() -> dict[str, Any]:
    """Return a compact inventory of the tracked evaluation artifacts."""

    scenarios = load_demo_scenarios()
    queries = load_retrieval_queries()
    qrels = load_retrieval_qrels()
    answer_cases = load_answer_eval_cases()

    return {
        "scenario_count": len(scenarios),
        "retrieval_query_count": len(queries),
        "retrieval_qrel_count": len(qrels),
        "answer_case_count": len(answer_cases),
        "retrieval_query_ids": [record["id"] for record in queries],
        "answer_case_ids": [record["id"] for record in answer_cases],
    }


if __name__ == "__main__":
    print(json.dumps(build_eval_inventory(), ensure_ascii=False, indent=2))
