"""Tests for local generation runtime configuration."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from types import SimpleNamespace

from backend.app.config import settings
from backend.scripts import build_retrieval_index
from backend.scripts import run_local_generation_server
from backend.scripts import setup_local_models


def test_qwen35_generator_defaults_target_small_cpu_runtime() -> None:
    assert settings.generation_model_name == "Qwen/Qwen3.5-9B"
    assert settings.generation_model_artifact == "unsloth/Qwen3.5-9B-GGUF:UD-Q6_K_XL"
    assert settings.generation_context_length == 4096
    assert settings.generation_enable_thinking is False
    assert settings.generation_temperature == 0.7
    assert settings.generation_top_p == 0.95
    assert settings.generation_top_k == 20
    assert settings.generation_min_p == 0.0
    assert settings.generation_presence_penalty == 1.5
    assert settings.generation_repeat_penalty == 1.15
    assert settings.generation_answer_max_tokens == 1024
    assert settings.generation_plan_max_tokens == 768
    assert settings.generation_skill_enrichment_max_tokens == 384
    assert settings.generation_request_timeout_seconds == 180.0
    assert settings.retrieval_embedding_device == "cpu"


def test_build_retrieval_index_accepts_standalone_cuda_override(monkeypatch) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        ["build_retrieval_index", "--force", "--device", "cuda", "--batch-size", "64"],
    )

    args = build_retrieval_index.parse_args()

    assert args.force is True
    assert args.device == "cuda"
    assert args.batch_size == 64


def test_setup_script_downloads_qwen35_q6_artifact() -> None:
    assert setup_local_models.GENERATOR_REPO_ID == "unsloth/Qwen3.5-9B-GGUF"
    assert setup_local_models.GENERATOR_LOCAL_DIR_NAME == "Qwen3.5-9B-GGUF"
    assert setup_local_models.GENERATOR_GGUF_PATTERN == "*UD-Q6_K_XL.gguf"
    assert "*UD-Q6_K_XL.gguf" in setup_local_models.GENERATOR_ALLOW_PATTERNS
    assert "tokenizer*" in setup_local_models.GENERATOR_ALLOW_PATTERNS


def test_llama_cpp_server_example_caps_context_and_threads() -> None:
    payload = json.loads(setup_local_models.CONFIG_DIR.joinpath("llama_cpp_python_server.example.json").read_text())
    model_config = payload["models"][0]

    assert model_config["model"].endswith("Qwen3.5-9B-UD-Q6_K_XL.gguf")
    assert model_config["model_alias"] == "unsloth/Qwen3.5-9B-GGUF:UD-Q6_K_XL"
    assert model_config["n_ctx"] == 4096
    assert model_config["n_gpu_layers"] == -1
    assert model_config["n_threads"] == 4
    assert model_config["flash_attn"] is True
    assert model_config["chat_template_kwargs"]["enable_thinking"] is False


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


def test_local_generation_server_applies_thinking_env_override(
    tmp_path: Path,
    monkeypatch,
) -> None:
    config_path = tmp_path / "llama_cpp_python_server.local.json"
    config_path.write_text(
        json.dumps(
            {
                "models": [
                    {
                        "model": str(tmp_path / "model.gguf"),
                        "model_alias": "test-model",
                        "chat_template_kwargs": {"enable_thinking": True},
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv(run_local_generation_server.THINKING_ENV, "false")

    runtime_path, payload = run_local_generation_server.prepare_runtime_config(config_path)

    assert payload["models"][0]["chat_template_kwargs"]["enable_thinking"] is False
    assert json.loads(runtime_path.read_text(encoding="utf-8"))["models"][0]["chat_template_kwargs"][
        "enable_thinking"
    ] is False


def test_local_generation_server_can_enable_thinking_with_env_override(
    tmp_path: Path,
    monkeypatch,
) -> None:
    config_path = tmp_path / "llama_cpp_python_server.local.json"
    config_path.write_text(
        json.dumps(
            {
                "models": [
                    {
                        "model": str(tmp_path / "model.gguf"),
                        "model_alias": "test-model",
                        "chat_template_kwargs": {"enable_thinking": False},
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv(run_local_generation_server.THINKING_ENV, "true")

    _runtime_path, payload = run_local_generation_server.prepare_runtime_config(config_path)

    assert payload["models"][0]["chat_template_kwargs"]["enable_thinking"] is True


def test_local_generation_server_requires_qwen35_capable_llama_cpp_python() -> None:
    assert run_local_generation_server.MIN_LLAMA_CPP_PYTHON_VERSION == "0.3.25"
    assert run_local_generation_server._version_tuple("0.3.25") >= run_local_generation_server._version_tuple(
        "0.3.21"
    )


def test_gpu_offload_requirement_reads_environment() -> None:
    assert run_local_generation_server.gpu_offload_required(
        {run_local_generation_server.REQUIRE_GPU_ENV: "true"}
    )
    assert not run_local_generation_server.gpu_offload_required({})


def test_llama_cpp_gpu_offload_probe_uses_binding_function() -> None:
    assert run_local_generation_server.llama_cpp_supports_gpu_offload(
        SimpleNamespace(llama_supports_gpu_offload=lambda: True)
    )
    assert not run_local_generation_server.llama_cpp_supports_gpu_offload(SimpleNamespace())
