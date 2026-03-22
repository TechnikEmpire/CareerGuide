"""Evaluation runner placeholder."""

from __future__ import annotations

import json
from pathlib import Path


def load_scenarios() -> list[dict[str, str]]:
    """Load static evaluation scenarios for the scaffold stage."""

    scenario_path = Path(__file__).with_name("scenarios.json")
    return json.loads(scenario_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    scenarios = load_scenarios()
    print(f"Loaded {len(scenarios)} evaluation scenarios.")
