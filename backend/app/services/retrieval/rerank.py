"""Reranking providers for dense candidate refinement."""

from __future__ import annotations

from collections.abc import Sequence
from functools import lru_cache
from typing import Protocol

from backend.app.config import settings

_SYSTEM_PROMPT = (
    'Judge whether the Document meets the requirements based on the Query '
    'and the Instruct provided. Note that the answer can only be "yes" or "no".'
)


class RerankerProvider(Protocol):
    """Minimal interface for query-document reranking."""

    model_id: str

    def rerank(self, query: str, documents: Sequence[str]) -> list[float]:
        """Return one relevance score per candidate document."""


def _token_counts(text: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for raw_token in text.lower().split():
        token = "".join(character for character in raw_token if character.isalnum())
        if not token:
            continue
        counts[token] = counts.get(token, 0) + 1
    return counts


def _overlap_score(query: str, document: str) -> float:
    query_counts = _token_counts(query)
    document_counts = _token_counts(document)
    if not query_counts or not document_counts:
        return 0.0

    overlap = sum(min(count, document_counts.get(token, 0)) for token, count in query_counts.items())
    normalizer = max(sum(query_counts.values()), 1)
    return overlap / normalizer


class DeterministicRerankerProvider:
    """Simple overlap reranker for tests and offline fallback."""

    model_id = "deterministic-reranker"

    def rerank(self, query: str, documents: Sequence[str]) -> list[float]:
        return [_overlap_score(query, document) for document in documents]


class Qwen3RerankerProvider:
    """Qwen3-based passage reranker using the official yes/no scoring pattern."""

    def __init__(self) -> None:
        self.model_id = settings.retrieval_reranker_model_id
        self.model_source = settings.retrieval_reranker_model_name
        self._tokenizer = None
        self._model = None
        self._torch = None
        self._prefix_tokens: list[int] | None = None
        self._suffix_tokens: list[int] | None = None
        self._token_true_id: int | None = None
        self._token_false_id: int | None = None

    def rerank(self, query: str, documents: Sequence[str]) -> list[float]:
        if not documents:
            return []

        self._ensure_model()
        assert self._torch is not None
        assert self._tokenizer is not None
        assert self._model is not None
        assert self._prefix_tokens is not None
        assert self._suffix_tokens is not None
        assert self._token_true_id is not None
        assert self._token_false_id is not None

        formatted_pairs = [
            self._format_pair(query=query, document=document)
            for document in documents
        ]

        scores: list[float] = []
        with self._torch.inference_mode():
            for start in range(0, len(formatted_pairs), settings.retrieval_reranker_batch_size):
                batch = formatted_pairs[start : start + settings.retrieval_reranker_batch_size]
                inputs = self._process_inputs(batch)
                logits = self._model(**inputs).logits[:, -1, :]
                false_logits = logits[:, self._token_false_id]
                true_logits = logits[:, self._token_true_id]
                pair_logits = self._torch.stack([false_logits, true_logits], dim=1)
                probabilities = self._torch.nn.functional.softmax(pair_logits, dim=1)[:, 1]
                scores.extend(probabilities.detach().cpu().tolist())

        return scores

    def _ensure_model(self) -> None:
        if self._model is not None and self._tokenizer is not None:
            return

        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as exc:
            raise RuntimeError(
                "Qwen3 reranking requires `transformers` and `torch`. "
                "Install the backend requirements before enabling the qwen3 reranker."
            ) from exc

        tokenizer = AutoTokenizer.from_pretrained(self.model_source, padding_side="left")
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        model_kwargs: dict[str, object] = {}
        device = "cuda" if torch.cuda.is_available() else "cpu"
        if torch.cuda.is_available():
            model_kwargs["dtype"] = torch.float16
        model = AutoModelForCausalLM.from_pretrained(self.model_source, **model_kwargs).to(device).eval()

        prefix = f"<|im_start|>system\n{_SYSTEM_PROMPT}<|im_end|>\n<|im_start|>user\n"
        suffix = "<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"

        self._torch = torch
        self._tokenizer = tokenizer
        self._model = model
        self._prefix_tokens = tokenizer.encode(prefix, add_special_tokens=False)
        self._suffix_tokens = tokenizer.encode(suffix, add_special_tokens=False)
        self._token_false_id = tokenizer.convert_tokens_to_ids("no")
        self._token_true_id = tokenizer.convert_tokens_to_ids("yes")

    def _format_pair(self, query: str, document: str) -> str:
        return (
            f"<Instruct>: {settings.retrieval_query_instruction}\n"
            f"<Query>: {query}\n"
            f"<Document>: {document}"
        )

    def _process_inputs(self, texts: Sequence[str]) -> dict[str, object]:
        assert self._tokenizer is not None
        assert self._model is not None
        assert self._prefix_tokens is not None
        assert self._suffix_tokens is not None

        available_length = settings.retrieval_reranker_max_length - len(self._prefix_tokens) - len(self._suffix_tokens)
        inputs = self._tokenizer(
            list(texts),
            padding=False,
            truncation="longest_first",
            return_attention_mask=False,
            max_length=max(available_length, 128),
        )
        for index, token_ids in enumerate(inputs["input_ids"]):
            inputs["input_ids"][index] = self._prefix_tokens + token_ids + self._suffix_tokens

        padded = self._tokenizer.pad(
            inputs,
            padding=True,
            return_tensors="pt",
            max_length=settings.retrieval_reranker_max_length,
        )
        return {key: value.to(self._model.device) for key, value in padded.items()}


@lru_cache(maxsize=1)
def get_reranker_provider() -> RerankerProvider:
    """Return the configured reranker provider."""

    provider_name = settings.retrieval_reranker_provider.lower()
    if provider_name == "deterministic":
        return DeterministicRerankerProvider()
    if provider_name == "qwen3":
        return Qwen3RerankerProvider()
    raise ValueError(f"Unsupported reranker provider: {settings.retrieval_reranker_provider}")
