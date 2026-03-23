"""Runtime loader for the tracked sentence-level memory classifier."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from backend.app.config import settings


@lru_cache(maxsize=4)
def _load_runtime_classifier_bundle(model_path: str, device: str):
    bundle_path = Path(model_path)
    if not bundle_path.exists():
        raise FileNotFoundError(
            "Runtime memory-classifier bundle was not found at "
            f"{bundle_path}. Train or restore the tracked binary bundle first."
        )

    try:
        from tooling.memory_extraction.classifier import load_classifier_bundle
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Runtime memory extraction requires the trained BiLSTM loader and its "
            "PyTorch dependency. Install the repo requirements before enabling "
            "the bilstm extraction backend."
        ) from exc

    return load_classifier_bundle(str(bundle_path), device=device)


def clear_runtime_classifier_cache() -> None:
    """Reset cached classifier bundles for tests."""

    _load_runtime_classifier_bundle.cache_clear()


def predict_runtime_memory_label(text: str) -> dict[str, Any]:
    """Run one segmented user sentence through the tracked binary bundle."""

    bundle = _load_runtime_classifier_bundle(
        str(settings.memory_extraction_model_path),
        settings.memory_extraction_device,
    )
    from tooling.memory_extraction.classifier import predict_single_text

    return predict_single_text(
        bundle=bundle,
        text=text,
        device=settings.memory_extraction_device,
    )
