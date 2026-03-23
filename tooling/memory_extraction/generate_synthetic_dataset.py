"""Generate a bilingual synthetic corpus for memory-extraction classification."""

from __future__ import annotations

import argparse
from collections import Counter
import json
import os
from pathlib import Path
import re
from typing import TYPE_CHECKING, Any
import uuid

import torch
from tqdm import tqdm

from tooling.memory_extraction.common import (
    append_jsonl,
    is_plausible_memory_example,
    looks_like_language,
    normalize_text,
    normalize_text_key,
    read_jsonl,
    tokenize_text,
    write_jsonl,
)
from tooling.memory_extraction.labels import MEMORY_EXTRACTION_LABELS, SUPPORTED_LANGUAGES
from tooling.memory_extraction.paths import RAW_SYNTHETIC_DATASET_PATH
from tooling.memory_extraction.prompts import PROMPT_NAME, build_generation_prompt
from tooling.memory_extraction.schema import MemoryExtractionRecord

if TYPE_CHECKING:
    from transformers import AutoModelForCausalLM, AutoTokenizer

DEFAULT_MODEL_SOURCE = "Qwen/Qwen3-0.6B"
_THINKING_PATTERN = re.compile(r"<think>.*?</think>", flags=re.DOTALL | re.IGNORECASE)
_EXAMPLES_TAG_PATTERN = re.compile(r"<examples>(.*?)</examples>", flags=re.DOTALL | re.IGNORECASE)
_LINE_PREFIX_PATTERN = re.compile(r"^\s*(?:[-*•]|\d+[.)]|[A-Za-zА-Яа-яЁё][.)])\s*")
_PREFIX_TOKEN_LIMIT = 4


def _load_transformers() -> tuple[type[Any], type[Any]]:
    """Import transformers lazily so parser-only utilities stay lightweight."""

    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except ImportError as exc:
        raise RuntimeError(
            "transformers is required for synthetic-data generation. "
            "Install the standalone tooling requirements first, for example:\n"
            "  python -m pip install -r tooling/memory_extraction/requirements.txt"
        ) from exc
    return AutoTokenizer, AutoModelForCausalLM


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a synthetic bilingual corpus for memory-extraction training."
    )
    parser.add_argument(
        "--output-jsonl",
        default=str(RAW_SYNTHETIC_DATASET_PATH),
        help="Where to write the synthetic JSONL corpus.",
    )
    parser.add_argument(
        "--model-source",
        default=DEFAULT_MODEL_SOURCE,
        help="Local path or Hugging Face model id for direct synthetic-data generation.",
    )
    parser.add_argument(
        "--local-files-only",
        action="store_true",
        help="Require model/tokenizer loading from local files only.",
    )
    parser.add_argument(
        "--languages",
        nargs="+",
        default=list(SUPPORTED_LANGUAGES),
        choices=SUPPORTED_LANGUAGES,
        help="Languages to generate.",
    )
    parser.add_argument(
        "--labels",
        nargs="+",
        default=MEMORY_EXTRACTION_LABELS,
        choices=MEMORY_EXTRACTION_LABELS,
        help="Labels to generate.",
    )
    parser.add_argument(
        "--examples-per-label",
        type=int,
        default=1000,
        help="Target number of examples for each language-label bucket.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="How many parallel single-example completions to sample per generation call.",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.7,
        help="Sampling temperature for synthetic generation.",
    )
    parser.add_argument(
        "--top-p",
        type=float,
        default=0.9,
        help="Top-p sampling parameter for synthetic generation.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=17,
        help="Random seed for reproducible sampling.",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=64,
        help="Maximum new tokens for one sampled example.",
    )
    parser.add_argument(
        "--device",
        default="auto",
        choices=("auto", "cuda", "cpu"),
        help="Execution device for direct generation.",
    )
    parser.add_argument(
        "--dtype",
        default="auto",
        choices=("auto", "float16", "bfloat16", "float32"),
        help="Torch dtype for model loading.",
    )
    parser.add_argument(
        "--compile",
        action="store_true",
        help="Compile the model forward pass with torch.compile when available.",
    )
    parser.add_argument(
        "--compile-mode",
        default="reduce-overhead",
        choices=("default", "reduce-overhead", "max-autotune", "max-autotune-no-cudagraphs"),
        help="torch.compile mode to use when --compile is enabled.",
    )
    parser.add_argument(
        "--attn-implementation",
        default="sdpa",
        choices=("sdpa", "eager"),
        help="Attention implementation to request from transformers.",
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help="Append to an existing dataset file instead of overwriting it.",
    )
    parser.add_argument(
        "--max-attempts-per-bucket",
        type=int,
        default=1000,
        help="Absolute safety limit on total generation attempts for one label-language bucket.",
    )
    parser.add_argument(
        "--max-stalled-attempts",
        type=int,
        default=40,
        help="Stop one label-language bucket after this many consecutive attempts with zero accepted examples.",
    )
    parser.add_argument(
        "--max-prefix-repeats",
        type=int,
        default=3,
        help="Reject accepted examples when too many start with the same first few tokens.",
    )
    parser.add_argument(
        "--near-duplicate-threshold",
        type=float,
        default=0.8,
        help="Reject examples whose token-set Jaccard similarity to an accepted example is above this threshold.",
    )
    return parser.parse_args()


def _extract_json_payload(raw_text: str) -> dict[str, object]:
    cleaned = _THINKING_PATTERN.sub("", raw_text)
    decoder = json.JSONDecoder()
    for start_index, character in enumerate(cleaned):
        if character != "{":
            continue
        try:
            payload, _ = decoder.raw_decode(cleaned[start_index:])
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            return payload

    excerpt = normalize_text(cleaned)[:400]
    raise ValueError(
        "The local generation model did not return a parseable JSON object. "
        f"Output excerpt: {excerpt!r}"
    )


def _iter_json_payloads(raw_text: str) -> list[object]:
    """Recover one or more JSON payloads from loose model output."""

    cleaned = _THINKING_PATTERN.sub("", raw_text)
    decoder = json.JSONDecoder()
    payloads: list[object] = []
    index = 0
    while index < len(cleaned):
        character = cleaned[index]
        if character not in "{[":
            index += 1
            continue
        try:
            payload, end_index = decoder.raw_decode(cleaned[index:])
        except json.JSONDecodeError:
            index += 1
            continue
        payloads.append(payload)
        index += end_index
        while index < len(cleaned) and cleaned[index] in " \t\r\n,":
            index += 1
    return payloads


def _normalize_example_line(line: str) -> str:
    """Strip light formatting noise from one generated sentence."""

    cleaned = normalize_text(line)
    cleaned = _LINE_PREFIX_PATTERN.sub("", cleaned)
    cleaned = cleaned.strip(" \"'`")
    return normalize_text(cleaned)


def _extract_examples_from_lines(raw_text: str) -> list[str]:
    """Recover one example sentence per line from loose model output."""

    cleaned = _THINKING_PATTERN.sub("", raw_text)
    tag_match = _EXAMPLES_TAG_PATTERN.search(cleaned)
    candidate_block = tag_match.group(1) if tag_match else cleaned

    examples: list[str] = []
    seen: set[str] = set()
    for raw_line in candidate_block.splitlines():
        line = _normalize_example_line(raw_line)
        if not line:
            continue
        lowered = line.casefold()
        if lowered.startswith(("examples:", "example:", "json", "{", "[")):
            continue
        if len(line.split()) < 3:
            continue
        if line in seen:
            continue
        seen.add(line)
        examples.append(line)
    return examples


def _extract_examples(raw_text: str) -> list[str]:
    """Recover generated examples from either JSON or line-based output."""

    cleaned_examples: list[str] = []
    seen: set[str] = set()
    for payload in _iter_json_payloads(raw_text):
        raw_examples: list[object] = []
        if isinstance(payload, dict):
            if isinstance(payload.get("examples"), list):
                raw_examples = list(payload["examples"])
            elif "text" in payload or "sentence" in payload:
                raw_examples = [payload]
        elif isinstance(payload, list):
            raw_examples = list(payload)

        for example in raw_examples:
            if isinstance(example, dict):
                text = _normalize_example_line(
                    str(example.get("text") or example.get("sentence") or "")
                )
            else:
                text = _normalize_example_line(str(example))
            if not text or text in seen:
                continue
            seen.add(text)
            cleaned_examples.append(text)

    if cleaned_examples:
        return cleaned_examples

    fallback_examples = _extract_examples_from_lines(raw_text)
    if fallback_examples:
        return fallback_examples

    excerpt = normalize_text(_THINKING_PATTERN.sub("", raw_text))[:400]
    raise ValueError(f"Could not recover examples from model output. Excerpt: {excerpt!r}")


def _candidate_prefix_key(text: str, *, token_limit: int = _PREFIX_TOKEN_LIMIT) -> tuple[str, ...]:
    """Build a lightweight prefix signature for diversity tracking."""

    tokens = tokenize_text(text)
    return tuple(tokens[:token_limit])


def _token_set_for_similarity(text: str) -> frozenset[str]:
    """Build a token set for cheap near-duplicate detection."""

    tokens = [token for token in tokenize_text(text) if any(character.isalpha() for character in token)]
    return frozenset(tokens)


def _jaccard_similarity(left: frozenset[str], right: frozenset[str]) -> float:
    """Compute token-set Jaccard similarity for two candidates."""

    if not left or not right:
        return 0.0
    union_size = len(left | right)
    if union_size == 0:
        return 0.0
    return len(left & right) / union_size


def _is_near_duplicate(
    token_set: frozenset[str],
    existing_sets: list[frozenset[str]],
    *,
    threshold: float,
) -> bool:
    """Return whether a candidate is too close to an already accepted example."""

    return any(_jaccard_similarity(token_set, existing_set) >= threshold for existing_set in existing_sets)


def _collect_avoid_phrases(
    *,
    accepted_prefix_counts: Counter[tuple[str, ...]],
    rejected_prefix_counts: Counter[tuple[str, ...]],
) -> tuple[str, ...]:
    """Build a short list of repeated openings to discourage in the next prompt."""

    scored_prefixes: Counter[tuple[str, ...]] = Counter()
    for prefix_key, count in accepted_prefix_counts.items():
        if len(prefix_key) >= 2 and count >= 2:
            scored_prefixes[prefix_key] += count
    for prefix_key, count in rejected_prefix_counts.items():
        if len(prefix_key) >= 2 and count >= 2:
            scored_prefixes[prefix_key] += count * 2
    return tuple(" ".join(prefix_key) for prefix_key, _ in scored_prefixes.most_common(4))


def _sampling_params_for_attempt(
    *,
    base_temperature: float,
    base_top_p: float,
    stalled_attempts: int,
) -> tuple[float, float, float]:
    """Increase exploration modestly when a bucket keeps stalling."""

    exploration_level = min(stalled_attempts // 6, 4)
    temperature = min(base_temperature + (0.1 * exploration_level), 1.15)
    top_p = min(base_top_p + (0.02 * exploration_level), 0.98)
    repetition_penalty = 1.05 + (0.03 * exploration_level)
    return temperature, top_p, repetition_penalty


def resolve_device(device_name: str) -> torch.device:
    """Resolve the requested device in a predictable way."""

    if device_name == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if device_name == "cuda":
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA was requested for synthetic-data generation, but no CUDA device is available.")
        return torch.device("cuda")
    return torch.device("cpu")


def resolve_dtype(dtype_name: str, device: torch.device) -> torch.dtype:
    """Resolve the requested torch dtype for local generation."""

    if dtype_name == "float16":
        return torch.float16
    if dtype_name == "bfloat16":
        return torch.bfloat16
    if dtype_name == "float32":
        return torch.float32
    if device.type == "cuda":
        if torch.cuda.is_bf16_supported():
            return torch.bfloat16
        return torch.float16
    return torch.float32


def build_model_and_tokenizer(
    *,
    model_source: str,
    device: torch.device,
    dtype: torch.dtype,
    compile_model: bool,
    compile_mode: str,
    attn_implementation: str,
    local_files_only: bool,
) -> tuple["AutoTokenizer", "AutoModelForCausalLM"]:
    """Load the local generation model directly into the tooling process."""

    AutoTokenizer, AutoModelForCausalLM = _load_transformers()

    model_source_path = Path(model_source)
    if model_source_path.suffix.lower() == ".gguf":
        raise RuntimeError(
            "The standalone synthetic-data generator uses transformers, not llama.cpp GGUF loading.\n"
            f"You passed a GGUF file: {model_source}\n"
            "Use either:\n"
            "  1. a Hugging Face model id such as `Qwen/Qwen3-0.6B`, or\n"
            "  2. a local transformers model directory containing files like "
            "`config.json`, tokenizer files, and model weights.\n"
            "A GGUF file is valid for the app's llama.cpp runtime, but not for this tooling."
        )
    looks_like_filesystem_path = (
        model_source.startswith((".", "/", "~"))
        or os.sep in model_source
        or (os.altsep is not None and os.altsep in model_source)
    )
    if looks_like_filesystem_path:
        resolved_path = model_source_path.expanduser()
        if not resolved_path.exists():
            raise RuntimeError(
                "The provided local model path does not exist:\n"
                f"  {resolved_path}\n"
                "Download the transformers model first, for example:\n"
                "  hf download Qwen/Qwen3-0.6B --local-dir models/Qwen3-0.6B"
            )
        if not resolved_path.is_dir():
            raise RuntimeError(
                "The provided local model path is not a directory:\n"
                f"  {resolved_path}\n"
                "Pass a transformers model directory, not a single file."
            )
        missing_files = [
            filename
            for filename in ("config.json", "tokenizer.json")
            if not (resolved_path / filename).exists()
        ]
        if missing_files:
            raise RuntimeError(
                "The provided local model directory is incomplete for transformers loading:\n"
                f"  {resolved_path}\n"
                "Missing required files:\n"
                + "".join(f"  - {filename}\n" for filename in missing_files)
                + "Download the full model directory first, for example:\n"
                "  hf download Qwen/Qwen3-0.6B --local-dir models/Qwen3-0.6B"
            )

    tokenizer = AutoTokenizer.from_pretrained(
        model_source,
        local_files_only=local_files_only,
    )
    if tokenizer.pad_token_id is None and tokenizer.eos_token_id is not None:
        tokenizer.pad_token = tokenizer.eos_token
    model_kwargs: dict[str, object] = {
        "torch_dtype": dtype,
        "attn_implementation": attn_implementation,
        "local_files_only": local_files_only,
    }
    if device.type == "cuda":
        model_kwargs["device_map"] = "auto"
    model = AutoModelForCausalLM.from_pretrained(model_source, **model_kwargs)
    if device.type != "cuda":
        model = model.to(device)
    if compile_model:
        if not hasattr(torch, "compile"):
            raise RuntimeError("torch.compile is not available in the installed PyTorch build.")
        model.forward = torch.compile(model.forward, mode=compile_mode)
    model.eval()
    return tokenizer, model


def _generate_examples(
    *,
    tokenizer: "AutoTokenizer",
    model: "AutoModelForCausalLM",
    device: torch.device,
    language: str,
    label: str,
    batch_size: int,
    temperature: float,
    top_p: float,
    max_tokens: int,
    repetition_penalty: float,
    variant_index: int,
    avoid_phrases: tuple[str, ...],
) -> list[str]:
    system_prompt = (
        "/no_think\n"
        "You generate clean synthetic datasets for sentence classification. "
        "Return exactly one plain example sentence. "
        "Do not add commentary, explanations, markdown, or surrounding prose. "
        "Vary the sentence openings and avoid repeating the same template."
    )
    user_prompt = build_generation_prompt(
        language=language,
        label=label,
        count=1,
        variant_index=variant_index,
        avoid_phrases=avoid_phrases,
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    prompt_text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )
    encoded = tokenizer(prompt_text, return_tensors="pt")
    encoded = {key: value.to(device if device.type != "cuda" else model.device) for key, value in encoded.items()}

    with torch.inference_mode():
        generated = model.generate(
            **encoded,
            num_return_sequences=batch_size,
            do_sample=True,
            temperature=temperature,
            top_p=top_p,
            max_new_tokens=max_tokens,
            repetition_penalty=repetition_penalty,
            pad_token_id=tokenizer.eos_token_id,
            use_cache=True,
        )
    prompt_length = encoded["input_ids"].shape[1]
    examples: list[str] = []
    for sequence in generated:
        new_tokens = sequence[prompt_length:]
        content = tokenizer.decode(new_tokens, skip_special_tokens=True)
        examples.extend(_extract_examples(str(content)))
    return examples


def main() -> None:
    args = parse_args()
    if args.max_attempts_per_bucket <= 0:
        raise ValueError("--max-attempts-per-bucket must be positive.")
    if args.max_stalled_attempts <= 0:
        raise ValueError("--max-stalled-attempts must be positive.")
    if args.max_prefix_repeats <= 0:
        raise ValueError("--max-prefix-repeats must be positive.")
    if not 0.0 < args.near_duplicate_threshold <= 1.0:
        raise ValueError("--near-duplicate-threshold must be in the interval (0, 1].")

    device = resolve_device(args.device)
    dtype = resolve_dtype(args.dtype, device)
    torch.manual_seed(args.seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(args.seed)
    tokenizer, model = build_model_and_tokenizer(
        model_source=args.model_source,
        device=device,
        dtype=dtype,
        compile_model=args.compile,
        compile_mode=args.compile_mode,
        attn_implementation=args.attn_implementation,
        local_files_only=args.local_files_only,
    )
    output_path = Path(args.output_jsonl)
    existing_records = read_jsonl(output_path) if args.append and output_path.exists() else []
    normalized_seen = {normalize_text_key(record.text) for record in existing_records}
    records = list(existing_records)
    if not args.append:
        write_jsonl(output_path, [])

    if device.type == "cuda":
        print(f"Using CUDA device: {torch.cuda.get_device_name(0)}")
    else:
        print("Using CPU generation path.")
    print(f"Model source: {args.model_source}")
    print(f"Model dtype: {dtype}")
    print(f"Local files only: {args.local_files_only}")
    print(f"Seed: {args.seed}")
    print(f"Max stalled attempts per bucket: {args.max_stalled_attempts}")
    if args.compile:
        print(f"torch.compile enabled with mode: {args.compile_mode}")

    for language in args.languages:
        for label in args.labels:
            bucket_records = [
                record
                for record in records
                if record.language == language and record.label == label
            ]
            existing_count = len(bucket_records)
            remaining = max(0, args.examples_per_label - existing_count)
            if remaining == 0:
                continue

            bucket_token_sets = [_token_set_for_similarity(record.text) for record in bucket_records]
            bucket_prefix_counts: Counter[tuple[str, ...]] = Counter(
                _candidate_prefix_key(record.text) for record in bucket_records
            )
            duplicate_prefix_counts: Counter[tuple[str, ...]] = Counter()
            progress = tqdm(total=remaining, desc=f"{language}:{label}", unit="example")
            attempts = 0
            stalled_attempts = 0
            rejection_counts: Counter[str] = Counter()
            try:
                while (
                    remaining > 0
                    and attempts < args.max_attempts_per_bucket
                    and stalled_attempts < args.max_stalled_attempts
                ):
                    attempts += 1
                    requested = min(args.batch_size, remaining)
                    avoid_phrases = _collect_avoid_phrases(
                        accepted_prefix_counts=bucket_prefix_counts,
                        rejected_prefix_counts=duplicate_prefix_counts,
                    )
                    temperature, top_p, repetition_penalty = _sampling_params_for_attempt(
                        base_temperature=args.temperature,
                        base_top_p=args.top_p,
                        stalled_attempts=stalled_attempts,
                    )
                    try:
                        generated_examples = _generate_examples(
                            tokenizer=tokenizer,
                            model=model,
                            device=device,
                            language=language,
                            label=label,
                            batch_size=requested,
                            temperature=temperature,
                            top_p=top_p,
                            max_tokens=args.max_tokens,
                            repetition_penalty=repetition_penalty,
                            variant_index=attempts - 1,
                            avoid_phrases=avoid_phrases,
                        )
                    except Exception as exc:
                        stalled_attempts += 1
                        rejection_counts["generation_error"] += 1
                        print(
                            f"Warning: generation failed for bucket {language}:{label} "
                            f"on attempt {attempts}: {exc}"
                        )
                        continue
                    accepted = 0
                    new_records: list[MemoryExtractionRecord] = []
                    for text in generated_examples:
                        prefix_key = _candidate_prefix_key(text)
                        if not looks_like_language(text, language):
                            rejection_counts["language"] += 1
                            continue
                        if not is_plausible_memory_example(text, language, label):
                            rejection_counts["semantic"] += 1
                            continue
                        normalized_key = normalize_text_key(text)
                        if normalized_key in normalized_seen:
                            rejection_counts["duplicate"] += 1
                            if prefix_key:
                                duplicate_prefix_counts[prefix_key] += 1
                            continue
                        token_set = _token_set_for_similarity(text)
                        if _is_near_duplicate(
                            token_set,
                            bucket_token_sets,
                            threshold=args.near_duplicate_threshold,
                        ):
                            rejection_counts["near_duplicate"] += 1
                            if prefix_key:
                                duplicate_prefix_counts[prefix_key] += 1
                            continue
                        if prefix_key and bucket_prefix_counts[prefix_key] >= args.max_prefix_repeats:
                            rejection_counts["prefix_repeat"] += 1
                            duplicate_prefix_counts[prefix_key] += 1
                            continue
                        normalized_seen.add(normalized_key)
                        bucket_token_sets.append(token_set)
                        if prefix_key:
                            bucket_prefix_counts[prefix_key] += 1
                        new_records.append(
                            MemoryExtractionRecord(
                                record_id=str(uuid.uuid4()),
                                language=language,
                                label=label,
                                text=text,
                                source="synthetic_local_qwen3",
                                source_model=args.model_source,
                                prompt_name=PROMPT_NAME,
                            )
                        )
                        accepted += 1
                    if new_records:
                        records.extend(new_records)
                        append_jsonl(output_path, new_records)
                    if accepted == 0:
                        stalled_attempts += 1
                    else:
                        stalled_attempts = 0
                    remaining -= accepted
                    progress.update(accepted)
                    progress.set_postfix(
                        attempts=attempts,
                        stalled=stalled_attempts,
                        dup=rejection_counts.get("duplicate", 0),
                        near=rejection_counts.get("near_duplicate", 0),
                    )
            finally:
                progress.close()
            if remaining > 0:
                stop_reason = (
                    "stall limit"
                    if stalled_attempts >= args.max_stalled_attempts
                    else "attempt limit"
                )
                print(
                    f"Warning: bucket {language}:{label} stopped with {remaining} missing "
                    f"examples after {attempts} attempts ({stop_reason})."
                )
            if rejection_counts:
                print(
                    f"Bucket diagnostics for {language}:{label}: "
                    + ", ".join(f"{reason}={count}" for reason, count in sorted(rejection_counts.items()))
                )
    print(f"Synthetic dataset written to: {output_path}")
    print(f"Total records: {len(records)}")


if __name__ == "__main__":
    main()
