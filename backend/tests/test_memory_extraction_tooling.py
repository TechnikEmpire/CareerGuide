"""Lightweight tests for standalone memory-extraction tooling."""

from __future__ import annotations

import torch

from tooling.memory_extraction.classifier import (
    BiLSTMMemoryClassifier,
    build_vocabulary,
    default_label_to_id,
    load_classifier_bundle,
    predict_single_text,
    save_classifier_bundle,
)
from tooling.memory_extraction.common import looks_like_language
from tooling.memory_extraction.common import is_plausible_memory_example
from tooling.memory_extraction.generate_synthetic_dataset import (
    _candidate_prefix_key,
    _extract_examples,
    _extract_json_payload,
    _is_near_duplicate,
    _token_set_for_similarity,
    resolve_device,
    resolve_dtype,
)
from tooling.memory_extraction.labels import (
    BINARY_MEMORY_EXTRACTION_LABELS,
    MEMORY_EXTRACTION_LABELS,
    MemoryBinaryLabel,
    MemoryExtractionLabel,
    derive_task_label,
    is_memorable_label,
)
from tooling.memory_extraction.prepare_dataset import project_records_for_task, split_records
from tooling.memory_extraction.prompts import build_generation_prompt
from tooling.memory_extraction.schema import MemoryExtractionRecord


def _record(record_id: str, language: str, label: str, text: str) -> MemoryExtractionRecord:
    return MemoryExtractionRecord(
        record_id=record_id,
        language=language,
        label=label,
        text=text,
        source="test",
        source_model="test-model",
        prompt_name="test-prompt",
    )


def test_label_schema_is_fixed_and_no_memory_is_not_persisted() -> None:
    """The current label schema should stay small and explicit."""

    assert MEMORY_EXTRACTION_LABELS == [
        MemoryExtractionLabel.NO_MEMORY.value,
        MemoryExtractionLabel.PREFERENCE.value,
        MemoryExtractionLabel.CONSTRAINT.value,
        MemoryExtractionLabel.GOAL.value,
        MemoryExtractionLabel.AVAILABILITY.value,
    ]
    assert not is_memorable_label(MemoryExtractionLabel.NO_MEMORY.value)
    assert is_memorable_label(MemoryExtractionLabel.CONSTRAINT.value)


def test_generation_prompt_mentions_label_and_language() -> None:
    """Synthetic prompts should stay explicit about the requested bucket."""

    prompt = build_generation_prompt(
        language="ru",
        label=MemoryExtractionLabel.CONSTRAINT.value,
        count=12,
    )
    assert "Russian" in prompt
    assert MemoryExtractionLabel.CONSTRAINT.value in prompt
    assert "exactly 12" in prompt
    assert "user utterance" in prompt
    assert "Do not write generic advice" in prompt


def test_generation_prompt_can_rotate_examples_and_avoid_repeated_openings() -> None:
    """Prompt building should support variant rotation and anti-collapse hints."""

    prompt = build_generation_prompt(
        language="ru",
        label=MemoryExtractionLabel.PREFERENCE.value,
        count=1,
        variant_index=3,
        avoid_phrases=("я предпочитаю плавную работу",),
    )

    assert "Avoid sentence openings or phrasings too close to" in prompt
    assert "я предпочитаю плавную работу" in prompt
    assert "Try to cover varied angles such as" in prompt


def test_direct_generation_device_and_dtype_resolution_support_cpu() -> None:
    """Standalone generation should allow explicit local device control."""

    device = resolve_device("cpu")
    dtype = resolve_dtype("float32", device)
    assert str(device) == "cpu"
    assert dtype == torch.float32


def test_json_payload_recovery_tolerates_trailing_text() -> None:
    """Synthetic generation parsing should survive extra trailing text."""

    payload = _extract_json_payload(
        '{"examples":[{"text":"I prefer remote work."}]} trailing junk'
    )
    assert payload["examples"] == [{"text": "I prefer remote work."}]


def test_example_recovery_accepts_plain_line_output() -> None:
    """Synthetic generation should tolerate plain one-sentence-per-line output."""

    examples = _extract_examples(
        "1. Я предпочитаю удаленную работу.\n"
        "2. Мне нужен спокойный переход в аналитику данных.\n"
        "3. Я не могу тратить больше 4 часов в неделю на обучение."
    )
    assert len(examples) == 3
    assert examples[0] == "Я предпочитаю удаленную работу."


def test_example_recovery_accepts_concatenated_sentence_objects() -> None:
    """Synthetic generation should recover examples from loose JSON-object streams."""

    examples = _extract_examples(
        '{"sentence": "Учиться — это важная задача для развития.", "label": "NO_MEMORY"} '
        '{"sentence": "Планирование карьеры помогает оценивать возможные шаги.", "label": "NO_MEMORY"}'
    )
    assert len(examples) == 2
    assert examples[0] == "Учиться — это важная задача для развития."


def test_language_quality_checks_are_simple_but_directionally_correct() -> None:
    """The synthetic quality gate should reject obvious language mismatches."""

    assert looks_like_language("Я предпочитаю удаленную работу.", "ru")
    assert not looks_like_language("I prefer remote work.", "ru")
    assert looks_like_language("I prefer remote work.", "en")
    assert not looks_like_language("Я предпочитаю удаленную работу.", "en")


def test_semantic_gate_accepts_clean_positive_examples() -> None:
    """The synthetic corpus gate should keep plausible user utterances."""

    assert is_plausible_memory_example(
        "Я не могу переезжать в другой город из-за семьи.",
        "ru",
        MemoryExtractionLabel.CONSTRAINT.value,
    )
    assert is_plausible_memory_example(
        "У меня есть только четыре часа в неделю на обучение.",
        "ru",
        MemoryExtractionLabel.AVAILABILITY.value,
    )
    assert is_plausible_memory_example(
        "I prefer remote work over daily office attendance.",
        "en",
        MemoryExtractionLabel.PREFERENCE.value,
    )


def test_semantic_gate_rejects_chain_of_thought_and_prompt_leakage() -> None:
    """The synthetic corpus gate should block obvious meta-output."""

    assert not is_plausible_memory_example(
        "For example, \"Я не могу работать без отдыха\". That translates to a work constraint.",
        "ru",
        MemoryExtractionLabel.CONSTRAINT.value,
    )
    assert not is_plausible_memory_example(
        "First, the sentence needs to express a hard limit.",
        "en",
        MemoryExtractionLabel.CONSTRAINT.value,
    )
    assert not is_plausible_memory_example(
        "Wait, the label should be obvious enough for classification.",
        "en",
        MemoryExtractionLabel.GOAL.value,
    )
    assert not is_plausible_memory_example(
        "Я не уверен, что я могу сохранить это в долгосрочной памяти.",
        "ru",
        MemoryExtractionLabel.NO_MEMORY.value,
    )


def test_semantic_gate_rejects_incomplete_or_known_artifact_phrasings() -> None:
    """The synthetic corpus gate should catch common small-model junk."""

    assert not is_plausible_memory_example(
        "Когда я только начинаю изучать разные карьерные варианты.",
        "ru",
        MemoryExtractionLabel.NO_MEMORY.value,
    )
    assert not is_plausible_memory_example(
        "Я предпочитаю рабочую работу в удаленной среде.",
        "ru",
        MemoryExtractionLabel.PREFERENCE.value,
    )
    assert not is_plausible_memory_example(
        "I prefer to do the work in a remote environment.",
        "en",
        MemoryExtractionLabel.PREFERENCE.value,
    )


def test_semantic_gate_rejects_wrong_label_signal() -> None:
    """The synthetic corpus gate should not become a hidden keyword classifier."""

    assert is_plausible_memory_example(
        "Важно учитывать работу и учебу для достижения целей в карьере.",
        "ru",
        MemoryExtractionLabel.PREFERENCE.value,
    )
    assert is_plausible_memory_example(
        "I want to move into cybersecurity next year.",
        "en",
        MemoryExtractionLabel.NO_MEMORY.value,
    )


def test_binary_task_projection_collapses_positive_labels() -> None:
    """Binary training should collapse all positive raw labels into MEMORY."""

    records = [
        _record("1", "ru", MemoryExtractionLabel.NO_MEMORY.value, "Какие навыки нужны?"),
        _record("2", "ru", MemoryExtractionLabel.GOAL.value, "Я хочу перейти в аналитику данных."),
        _record("3", "en", MemoryExtractionLabel.CONSTRAINT.value, "I cannot relocate."),
    ]
    projected = project_records_for_task(records, task="binary")

    assert [record.label for record in projected] == [
        MemoryBinaryLabel.NO_MEMORY.value,
        MemoryBinaryLabel.MEMORY.value,
        MemoryBinaryLabel.MEMORY.value,
    ]
    assert derive_task_label(MemoryExtractionLabel.PREFERENCE.value, "binary") == MemoryBinaryLabel.MEMORY.value


def test_generation_diversity_helpers_detect_prefix_repetition_and_near_duplicates() -> None:
    """Synthetic generation should detect templatic collapse beyond exact string matches."""

    assert _candidate_prefix_key("Я не могу переезжать в другой город из-за семьи.") == (
        "я",
        "не",
        "могу",
        "переезжать",
    )
    existing = [_token_set_for_similarity("Я не могу переезжать в другой город из-за семьи.")]
    candidate = _token_set_for_similarity("Я не могу переехать в другой город из-за семьи.")
    assert _is_near_duplicate(candidate, existing, threshold=0.8)


def test_split_records_preserves_each_language_label_bucket() -> None:
    """Prepared splits should keep every label-language bucket represented."""

    records = []
    for language, text_prefix in [("ru", "текст"), ("en", "text")]:
        for label in MEMORY_EXTRACTION_LABELS:
            for index in range(10):
                records.append(
                    _record(
                        record_id=f"{language}-{label}-{index}",
                        language=language,
                        label=label,
                        text=f"{text_prefix} {label} {index}",
                    )
                )

    splits = split_records(records, seed=17, train_ratio=0.8, dev_ratio=0.1)

    for language in ("ru", "en"):
        for label in MEMORY_EXTRACTION_LABELS:
            assert any(
                record.language == language and record.label == label
                for record in splits["train"]
            )
            assert any(
                record.language == language and record.label == label
                for record in splits["test"]
            )


def test_bilstm_classifier_forward_shape_matches_label_count() -> None:
    """The binary BiLSTM head should emit one logit per derived task label."""

    records = [
        _record("1", "en", MemoryExtractionLabel.PREFERENCE.value, "I prefer remote work."),
        _record("2", "ru", MemoryExtractionLabel.GOAL.value, "Я хочу перейти в аналитику данных."),
    ]
    token_to_id = build_vocabulary(records)
    model = BiLSTMMemoryClassifier(
        vocab_size=len(token_to_id),
        embedding_dim=16,
        hidden_dim=8,
        label_count=len(BINARY_MEMORY_EXTRACTION_LABELS),
        dropout=0.1,
    )
    token_ids = torch.tensor([[2, 3, 4], [2, 5, 6]], dtype=torch.long)
    lengths = torch.tensor([3, 3], dtype=torch.long)

    logits = model(token_ids, lengths)
    assert logits.shape == (2, len(BINARY_MEMORY_EXTRACTION_LABELS))


def test_classifier_bundle_round_trip_returns_valid_prediction(tmp_path) -> None:
    """Saved classifier bundles should reload cleanly for later inference."""

    records = [
        _record("1", "en", MemoryExtractionLabel.PREFERENCE.value, "I prefer remote work."),
        _record("2", "ru", MemoryExtractionLabel.GOAL.value, "Я хочу перейти в аналитику данных."),
    ]
    token_to_id = build_vocabulary(records)
    label_to_id = default_label_to_id(task="binary")
    model = BiLSTMMemoryClassifier(
        vocab_size=len(token_to_id),
        embedding_dim=16,
        hidden_dim=8,
        label_count=len(BINARY_MEMORY_EXTRACTION_LABELS),
        dropout=0.1,
    )

    bundle_path = tmp_path / "memory_classifier.pt"
    save_classifier_bundle(
        path=str(bundle_path),
        model=model,
        token_to_id=token_to_id,
        label_to_id=label_to_id,
        config={
            "vocab_size": len(token_to_id),
            "embedding_dim": 16,
            "hidden_dim": 8,
            "dropout": 0.1,
            "task": "binary",
        },
    )

    loaded_bundle = load_classifier_bundle(str(bundle_path))
    prediction = predict_single_text(
        bundle=loaded_bundle,
        text="I prefer remote work.",
    )

    assert prediction["label"] in BINARY_MEMORY_EXTRACTION_LABELS
    assert 0.0 <= prediction["confidence"] <= 1.0
