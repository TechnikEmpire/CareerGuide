"""Tests for local generation runtime configuration."""

from __future__ import annotations

import json
from pathlib import Path

from backend.app.config import settings
from backend.scripts import run_local_generation_server
from backend.scripts import setup_local_models


def test_qwen35_generator_defaults_target_small_cpu_runtime() -> None:
    assert settings.generation_model_name == "Qwen/Qwen3.5-2B"
    assert settings.generation_model_artifact == "bartowski/Qwen_Qwen3.5-2B-GGUF:Q4_K_M"
    assert settings.generation_context_length == 8192
    assert settings.generation_plan_max_tokens == 768
    assert settings.generation_skill_enrichment_max_tokens == 384
    assert settings.generation_request_timeout_seconds == 180.0


def test_setup_script_downloads_qwen35_q4_artifact() -> None:
    assert setup_local_models.GENERATOR_REPO_ID == "bartowski/Qwen_Qwen3.5-2B-GGUF"
    assert setup_local_models.GENERATOR_LOCAL_DIR_NAME == "Qwen_Qwen3.5-2B-GGUF"
    assert setup_local_models.GENERATOR_GGUF_PATTERN == "*Q4_K_M.gguf"
    assert "*Q4_K_M.gguf" in setup_local_models.GENERATOR_ALLOW_PATTERNS
    assert "tokenizer*" in setup_local_models.GENERATOR_ALLOW_PATTERNS


def test_llama_cpp_server_example_caps_context_and_threads() -> None:
    payload = json.loads(setup_local_models.CONFIG_DIR.joinpath("llama_cpp_python_server.example.json").read_text())
    model_config = payload["models"][0]

    assert model_config["model"].endswith("Qwen_Qwen3.5-2B-Q4_K_M.gguf")
    assert model_config["model_alias"] == "bartowski/Qwen_Qwen3.5-2B-GGUF:Q4_K_M"
    assert model_config["n_ctx"] == 8192
    assert model_config["n_threads"] == 4
    assert model_config["flash_attn"] is True


def test_setup_script_forces_flash_attention_for_generated_config() -> None:
    payload = {"models": [{"model": "model.gguf"}, {"model": "other.gguf", "flash_attn": False}]}

    updated = setup_local_models.force_flash_attention(payload)

    assert all(model["flash_attn"] is True for model in updated["models"])


def test_local_generation_server_forces_flash_attention_for_stale_config(tmp_path: Path) -> None:
    config_path = tmp_path / "llama_cpp_python_server.local.json"
    config_path.write_text(
        json.dumps(
            {
                "models": [
                    {
                        "model": str(tmp_path / "model.gguf"),
                        "model_alias": "test-model",
                        "n_ctx": 8192,
                        "n_threads": 4,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    runtime_path, payload = run_local_generation_server.prepare_runtime_config(config_path)

    assert runtime_path.name == "llama_cpp_python_server.local.runtime.json"
    assert payload["models"][0]["flash_attn"] is True
    assert json.loads(runtime_path.read_text(encoding="utf-8"))["models"][0]["flash_attn"] is True


def test_local_generation_server_requires_qwen35_capable_llama_cpp_python() -> None:
    assert run_local_generation_server.MIN_LLAMA_CPP_PYTHON_VERSION == "0.3.21"
    assert run_local_generation_server._version_tuple("0.3.21") >= run_local_generation_server._version_tuple(
        "0.3.16"
    )
