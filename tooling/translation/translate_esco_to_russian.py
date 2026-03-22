"""Translate normalized ESCO concept records from English into derived Russian fields.

This script is intentionally standalone and resumable. It does not mutate the
canonical English source data. Instead, it reads normalized English concept
records and writes bilingual records that preserve both the source fields and the
derived Russian translations.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
import sys
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import torch
from tqdm import tqdm
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

from tooling.translation.common import append_jsonl, read_jsonl, write_json, write_jsonl
from tooling.translation.paths import (
    BILINGUAL_CONCEPTS_PATH,
    NORMALIZED_CONCEPTS_PATH,
    TRANSLATION_MANIFEST_PATH,
    ensure_processed_directories,
)


TRANSLATABLE_LIST_FIELDS = ("alt_labels", "hidden_labels")
TRANSLATABLE_TEXT_FIELDS = (
    "preferred_label",
    "description",
    "definition",
    "scope_note",
    "regulated_profession_note",
)


def build_model_and_tokenizer(
    model_name: str,
    source_lang: str,
    compile_model: bool,
    compile_mode: str,
) -> tuple[AutoTokenizer, AutoModelForSeq2SeqLM, torch.dtype]:
    """Load the translation model and tokenizer."""

    tokenizer = AutoTokenizer.from_pretrained(model_name, src_lang=source_lang)

    dtype = torch.float16 if torch.cuda.is_available() else torch.float32
    model = AutoModelForSeq2SeqLM.from_pretrained(
        model_name,
        dtype=dtype,
        device_map="auto" if torch.cuda.is_available() else None,
    )
    if compile_model:
        if not hasattr(torch, "compile"):
            raise RuntimeError("torch.compile is not available in the installed PyTorch build.")
        # Compiling the forward pass preserves the Hugging Face generation API
        # while giving PyTorch a chance to lower eager-mode overhead.
        model.forward = torch.compile(
            model.forward,
            mode=compile_mode,
        )
    model.eval()
    return tokenizer, model, dtype


def flatten_translatable_fields(record: dict[str, Any]) -> tuple[list[str], list[tuple[str, int | None]]]:
    """Flatten translatable text fields and preserve their output mapping."""

    source_text = record["source_text"]
    texts: list[str] = []
    mapping: list[tuple[str, int | None]] = []

    for field_name in TRANSLATABLE_TEXT_FIELDS:
        value = source_text.get(field_name)
        if value:
            texts.append(value)
            mapping.append((field_name, None))

    for field_name in TRANSLATABLE_LIST_FIELDS:
        values = source_text.get(field_name, [])
        for index, value in enumerate(values):
            if value:
                texts.append(value)
                mapping.append((field_name, index))

    return texts, mapping


def translate_text_batch(
    texts: list[str],
    tokenizer: AutoTokenizer,
    model: AutoModelForSeq2SeqLM,
    target_lang: str,
    max_source_length: int,
    max_new_tokens: int,
    num_beams: int,
    compile_model: bool,
) -> list[str]:
    """Translate one batch of texts from English into Russian.

    We use deterministic beam search because this is a one-time preprocessing
    task where repeatability and factual stability matter more than creative
    variation.
    """

    if not texts:
        return []

    encoded = tokenizer(
        texts,
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=max_source_length,
    )

    if torch.cuda.is_available():
        encoded = {key: value.to(model.device) for key, value in encoded.items()}

    if compile_model and hasattr(torch, "compiler") and hasattr(torch.compiler, "cudagraph_mark_step_begin"):
        torch.compiler.cudagraph_mark_step_begin()

    # Newer NLLB fast tokenizers no longer expose `lang_code_to_id`, so we
    # resolve the target language token id through the tokenizer's token-id
    # conversion path and keep the older attribute as a compatibility fallback.
    if hasattr(tokenizer, "lang_code_to_id"):
        forced_bos_token_id = tokenizer.lang_code_to_id[target_lang]
    else:
        forced_bos_token_id = tokenizer.convert_tokens_to_ids(target_lang)
        if forced_bos_token_id is None or forced_bos_token_id < 0:
            raise ValueError(f"Could not resolve target language token id for {target_lang!r}.")

    generated = model.generate(
        **encoded,
        forced_bos_token_id=forced_bos_token_id,
        max_new_tokens=max_new_tokens,
        num_beams=num_beams,
        do_sample=False,
    )
    return tokenizer.batch_decode(generated, skip_special_tokens=True)


def translate_text_batch_bucketed(
    texts: list[str],
    tokenizer: AutoTokenizer,
    model: AutoModelForSeq2SeqLM,
    target_lang: str,
    text_batch_size: int,
    max_source_length: int,
    max_new_tokens: int,
    num_beams: int,
    disable_length_bucketing: bool,
    compile_model: bool,
) -> list[str]:
    """Translate texts in chunks while reducing padding waste where possible."""

    if not texts:
        return []

    indexed_texts = list(enumerate(texts))
    if not disable_length_bucketing:
        indexed_texts.sort(key=lambda item: len(item[1]), reverse=True)

    translated_by_original_index: list[str | None] = [None] * len(texts)

    for start in range(0, len(indexed_texts), text_batch_size):
        chunk = indexed_texts[start : start + text_batch_size]
        chunk_texts = [text for _, text in chunk]
        translated_chunk = translate_text_batch(
            texts=chunk_texts,
            tokenizer=tokenizer,
            model=model,
            target_lang=target_lang,
            max_source_length=max_source_length,
            max_new_tokens=max_new_tokens,
            num_beams=num_beams,
            compile_model=compile_model,
        )
        for (original_index, _), translated_text in zip(chunk, translated_chunk, strict=True):
            translated_by_original_index[original_index] = translated_text

    return [text for text in translated_by_original_index if text is not None]


def apply_translations(record: dict[str, Any], mapping: list[tuple[str, int | None]], translated_texts: list[str], model_name: str) -> dict[str, Any]:
    """Attach derived Russian fields to one concept record."""

    translated_record = dict(record)
    translated_record["translations"] = {
        "ru": {
            "preferred_label": None,
            "alt_labels": [],
            "hidden_labels": [],
            "description": None,
            "definition": None,
            "scope_note": None,
            "regulated_profession_note": None,
            "translation_meta": {
                "model_name": model_name,
                "source_language": "eng_Latn",
                "target_language": "rus_Cyrl",
                "translated_at": datetime.now(UTC).isoformat(),
            },
        }
    }

    for (field_name, index), translated_text in zip(mapping, translated_texts, strict=True):
        if index is None:
            translated_record["translations"]["ru"][field_name] = translated_text
        else:
            translated_record["translations"]["ru"][field_name].append(translated_text)

    return translated_record


def choose_latest_record(existing: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    """Return the preferred record for a duplicate concept URI."""

    existing_modified = existing.get("audit", {}).get("modified_date") or ""
    candidate_modified = candidate.get("audit", {}).get("modified_date") or ""

    if candidate_modified >= existing_modified:
        preferred = deepcopy(candidate)
        fallback = existing
    else:
        preferred = deepcopy(existing)
        fallback = candidate

    preferred.setdefault("translations", {})
    fallback_translations = fallback.get("translations", {})
    if "ru" not in preferred["translations"] and "ru" in fallback_translations:
        preferred["translations"]["ru"] = fallback_translations["ru"]

    return preferred


def dedupe_records_by_uri(records: Iterable[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    """Collapse duplicate concept URIs while preserving stable output order."""

    records_by_uri: dict[str, dict[str, Any]] = {}
    uri_order: list[str] = []
    duplicate_rows_removed = 0

    for record in records:
        concept_uri = record.get("concept_uri")
        if not concept_uri:
            continue
        if concept_uri in records_by_uri:
            records_by_uri[concept_uri] = choose_latest_record(records_by_uri[concept_uri], record)
            duplicate_rows_removed += 1
            continue
        records_by_uri[concept_uri] = record
        uri_order.append(concept_uri)

    return [records_by_uri[concept_uri] for concept_uri in uri_order], duplicate_rows_removed


def compact_existing_bilingual_output(path: Path) -> int:
    """Rewrite the bilingual JSONL output in-place if duplicate URIs are present."""

    if not path.exists():
        return 0

    deduped_records, duplicate_rows_removed = dedupe_records_by_uri(read_jsonl(path))
    if duplicate_rows_removed > 0:
        write_path = path.with_suffix(path.suffix + ".tmp")
        write_jsonl(write_path, deduped_records)
        write_path.replace(path)
    return duplicate_rows_removed


def load_completed_uris(path: Path) -> set[str]:
    """Read already translated concept URIs so the run can resume safely."""

    if not path.exists():
        return set()

    completed = set()
    for record in read_jsonl(path):
        concept_uri = record.get("concept_uri")
        if concept_uri:
            completed.add(concept_uri)
    return completed


def iter_record_batches(records: Iterable[dict[str, Any]], batch_size: int) -> Iterable[list[dict[str, Any]]]:
    """Yield fixed-size batches of records."""

    batch: list[dict[str, Any]] = []
    for record in records:
        batch.append(record)
        if len(batch) >= batch_size:
            yield batch
            batch = []
    if batch:
        yield batch


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""

    parser = argparse.ArgumentParser(description="Translate normalized ESCO concepts into Russian.")
    parser.add_argument("--concepts-path", type=Path, default=NORMALIZED_CONCEPTS_PATH)
    parser.add_argument("--out-path", type=Path, default=BILINGUAL_CONCEPTS_PATH)
    parser.add_argument("--manifest-path", type=Path, default=TRANSLATION_MANIFEST_PATH)
    parser.add_argument("--model-name", default="facebook/nllb-200-3.3B")
    parser.add_argument("--source-lang", default="eng_Latn")
    parser.add_argument("--target-lang", default="rus_Cyrl")
    parser.add_argument("--record-batch-size", type=int, default=8)
    parser.add_argument("--text-batch-size", type=int, default=24)
    parser.add_argument("--max-source-length", type=int, default=512)
    parser.add_argument("--max-new-tokens", type=int, default=512)
    parser.add_argument("--num-beams", type=int, default=4)
    parser.add_argument(
        "--compile",
        action="store_true",
        help="Compile the model forward pass with torch.compile to reduce eager overhead.",
    )
    parser.add_argument(
        "--compile-mode",
        default="reduce-overhead",
        choices=("default", "reduce-overhead", "max-autotune", "max-autotune-no-cudagraphs"),
        help="torch.compile mode to use when --compile is enabled.",
    )
    parser.add_argument(
        "--disable-length-bucketing",
        action="store_true",
        help="Disable sorting texts by approximate length before translation batching.",
    )
    parser.add_argument("--limit", type=int, default=None, help="Optional limit for debugging or test runs.")
    parser.add_argument("--overwrite", action="store_true", help="Delete the previous bilingual output and start over.")
    return parser.parse_args()


def main() -> None:
    """Run the ESCO translation pipeline."""

    args = parse_args()
    ensure_processed_directories()

    if args.overwrite and args.out_path.exists():
        args.out_path.unlink()
    elif args.out_path.exists():
        duplicate_rows_removed = compact_existing_bilingual_output(args.out_path)
        if duplicate_rows_removed > 0:
            print(f"Compacted existing bilingual output by removing {duplicate_rows_removed} duplicate URI rows.")

    tokenizer, model, dtype = build_model_and_tokenizer(
        model_name=args.model_name,
        source_lang=args.source_lang,
        compile_model=args.compile,
        compile_mode=args.compile_mode,
    )

    if torch.cuda.is_available():
        print(f"Using CUDA device: {torch.cuda.get_device_name(0)}")
    else:
        print("Using CPU translation path.")
    print(f"Model dtype: {dtype}")
    print(f"Length bucketing: {not args.disable_length_bucketing}")
    if args.compile:
        print(f"torch.compile enabled with mode: {args.compile_mode}")

    completed_uris = load_completed_uris(args.out_path)
    all_records, duplicate_input_rows_removed = dedupe_records_by_uri(read_jsonl(args.concepts_path))
    if duplicate_input_rows_removed > 0:
        print(f"Deduplicated normalized concept input by removing {duplicate_input_rows_removed} duplicate URI rows.")
    if args.limit is not None:
        all_records = all_records[: args.limit]

    pending_records = [
        record for record in all_records if record.get("concept_uri") not in completed_uris
    ]

    translated_count = 0
    translated_field_count = 0
    run_started_at = datetime.now(UTC).isoformat()

    for record_batch in tqdm(
        list(iter_record_batches(pending_records, args.record_batch_size)),
        desc="Translating ESCO concepts",
    ):
        flattened_texts: list[str] = []
        record_mappings: list[tuple[dict[str, Any], list[tuple[str, int | None]], int, int]] = []

        for record in record_batch:
            texts, mapping = flatten_translatable_fields(record)
            start_index = len(flattened_texts)
            flattened_texts.extend(texts)
            end_index = len(flattened_texts)
            record_mappings.append((record, mapping, start_index, end_index))

        translated_flattened = translate_text_batch_bucketed(
            texts=flattened_texts,
            tokenizer=tokenizer,
            model=model,
            target_lang=args.target_lang,
            text_batch_size=args.text_batch_size,
            max_source_length=args.max_source_length,
            max_new_tokens=args.max_new_tokens,
            num_beams=args.num_beams,
            disable_length_bucketing=args.disable_length_bucketing,
            compile_model=args.compile,
        )

        translated_records = []
        for record, mapping, start_index, end_index in record_mappings:
            translated_record = apply_translations(
                record=record,
                mapping=mapping,
                translated_texts=translated_flattened[start_index:end_index],
                model_name=args.model_name,
            )
            translated_records.append(translated_record)
            translated_count += 1
            translated_field_count += len(mapping)

        append_jsonl(args.out_path, translated_records)

    manifest = {
        "dataset": "esco",
        "input_concepts_path": str(args.concepts_path),
        "output_concepts_path": str(args.out_path),
        "model_name": args.model_name,
        "source_lang": args.source_lang,
        "target_lang": args.target_lang,
        "record_batch_size": args.record_batch_size,
        "text_batch_size": args.text_batch_size,
        "max_source_length": args.max_source_length,
        "max_new_tokens": args.max_new_tokens,
        "num_beams": args.num_beams,
        "compile_enabled": args.compile,
        "compile_mode": args.compile_mode if args.compile else None,
        "length_bucketing_enabled": not args.disable_length_bucketing,
        "run_started_at": run_started_at,
        "run_completed_at": datetime.now(UTC).isoformat(),
        "records_seen": len(all_records),
        "records_previously_completed": len(completed_uris),
        "records_translated_this_run": translated_count,
        "translated_fields_this_run": translated_field_count,
        "duplicate_input_rows_removed": duplicate_input_rows_removed,
        "notes": [
            "Source English fields remain canonical.",
            "Russian fields are derived translations for one-time preprocessing.",
            "Relations remain language-neutral through concept URIs and should be joined against bilingual concept records later.",
        ],
    }
    write_json(args.manifest_path, manifest)

    print(f"Wrote bilingual concepts to: {args.out_path}")
    print(f"Wrote translation manifest to: {args.manifest_path}")
    print(f"Translated records this run: {translated_count}")


if __name__ == "__main__":
    main()
