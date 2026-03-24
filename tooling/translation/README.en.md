# ESCO Translation Tooling

### What This Directory Is For

This directory contains the standalone tooling for the one-time preprocessing of
the ESCO source data.

This stage happens before the application pipeline.

At this stage we are not yet:

- building the live retrieval pipeline
- creating app-ready chunks
- generating embeddings
- running reranking
- serving the web app

At this stage we are only:

1. reading the raw ESCO English CSV export
2. normalizing it into one common internal format
3. creating a derived Russian translation layer
4. writing bilingual artifacts into `data/processed/esco/`

The output of this tooling becomes the trusted bilingual source layer for the
later app pipeline.

### Current Expected Input

For this preprocessing stage, the expected input is the English classification
CSV export, not the large Local API package.

Current expected raw directory:

- `data/raw/ESCO/ESCO_dataset_v1.2.1_classification_en_csv/`

Important input files:

- `occupations_en.csv`
- `skills_en.csv`
- `occupationSkillRelations_en.csv`
- `skillSkillRelations_en.csv`
- `broaderRelationsOccPillar_en.csv`
- `broaderRelationsSkillPillar_en.csv`
- `ISCOGroups_en.csv`
- `skillGroups_en.csv`

If you are downloading ESCO specifically for this tooling, the practical choice
is:

1. `ESCO dataset`
2. `classification`
3. `en`
4. `csv`

The Local API package is not required for this preprocessing workflow.

### Why We Normalize Before We Translate

The repository must preserve the original ESCO source text and identifiers.

That means:

- English source data stays canonical.
- Russian is stored as a derived layer.
- Relations stay URI-first and language-neutral.
- Later pipeline stages can join bilingual concept records to relation records by URI.

This preserves:

- provenance
- citation fidelity
- reproducibility
- academic honesty

### Why ESCO URIs Matter

The ESCO URI is the stable identifier for a concept.

This matters because:

- occupations and skills are linked to the rest of the ESCO graph by URI
- relation files point to concept URIs rather than to translated labels
- the app will later join bilingual concept text back to the relation graph by URI

Without URIs, the project would have no stable way to connect:

- English source text
- Russian translated text
- occupation-skill relations
- hierarchy relations

### Important CSV Warning

These ESCO CSV files contain quoted multiline cells.

That is common in fields such as:

- `altLabels`
- `description`
- `scopeNote`
- `inScheme`

Because of that, raw line counts are not real record counts. These files must
be parsed with a real CSV parser. Do not process them with line splitting or
regex shortcuts.

The current vendor CSV also contains a small number of duplicate concept rows
with the same `conceptUri`. In this dump, those duplicate rows differ only by
`modifiedDate`. The normalizer collapses them by URI and keeps the latest
source row.

### Tooling Layout

- `normalize_esco_csv.py`
  Reads the raw English ESCO CSV files and writes normalized concept and
  relation JSONL artifacts.

- `translate_esco_to_russian.py`
  Reads normalized concept records and writes derived Russian translations into
  a bilingual JSONL artifact.

- `common.py`
  Shared helpers for CSV parsing, text cleanup, and JSON/JSONL output.

- `paths.py`
  Shared input and output paths used by the preprocessing tooling.

- `requirements.txt`
  Canonical WSL2/Linux workstation requirements for the standalone translation
  workflow, including a CUDA-enabled PyTorch baseline.

### Recommended Environment

This tooling is aimed at your workstation workflow, not the student's everyday
app-development environment.

The clean, reproducible path is a dedicated Conda environment on WSL2.

Recommended standalone tooling environment for an NVIDIA GPU workstation:

```bash
cd /mnt/e/Work-Repos-SiftVPN/CareerGuide
source ~/miniconda3/etc/profile.d/conda.sh

conda create -n careerguide-tools python=3.11 -y
conda activate careerguide-tools

python -m pip install --upgrade pip
python -m pip install -r tooling/translation/requirements.txt
```

Notes:

- `tooling/translation/requirements.txt` now includes the canonical GPU runtime baseline for this one-time translation workflow.
- The pinned baseline is PyTorch `2.6.0` from the CUDA `12.4` wheel index.
- This is a practical reproducibility choice for WSL2 plus a strong NVIDIA GPU such as an RTX 4090.
- The translation script automatically uses `float16` when CUDA is available.

If you want to reuse an existing CUDA-ready Conda environment instead of
creating a fresh one, verify the GPU first:

```bash
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CUDA not available')"
```

If that command reports a working CUDA device, you can keep that environment and
install only the non-torch extras:

```bash
python -m pip install --upgrade pip
python -m pip install "accelerate>=1.2,<2" "safetensors>=0.4,<1" "sentencepiece>=0.2,<1" "transformers>=4.48,<5" "tqdm>=4.66,<5"
```

For this repo, the authoritative clean-install path remains the dedicated
`careerguide-tools` environment above.

### Environment Verification

After installation, verify that PyTorch can see the GPU:

```bash
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CUDA not available')"
```

Expected result on a working workstation setup:

- a printed torch version
- `True` for `torch.cuda.is_available()`
- your GPU name, such as `NVIDIA GeForce RTX 4090`

### Recommended Translation Model

The default translation model in the script is:

- `facebook/nllb-200-3.3B`

Current default language codes:

- source: `eng_Latn`
- target: `rus_Cyrl`

Why this model:

- it is a translation model rather than a general chat model
- it is appropriate for one-time preprocessing on a strong workstation GPU
- it is a better quality choice than the smaller distilled variant for English-to-Russian translation

This model is used only for preprocessing. It is not the app's runtime
generator.

### Quick Start

#### Step 1. Normalize the raw ESCO CSV export

```bash
python -m tooling.translation.normalize_esco_csv
```

This reads from:

- `data/raw/ESCO/ESCO_dataset_v1.2.1_classification_en_csv/`

This writes:

- `data/processed/esco/normalized/esco_concepts.en.jsonl`
- `data/processed/esco/normalized/esco_relations.jsonl`
- `data/processed/esco/manifests/esco_normalization_stats.json`

Tracking policy for this step:

- `data/raw/ESCO/` remains ignored because it is a vendor download.
- `data/processed/esco/normalized/esco_concepts.en.jsonl` is tracked because it is the normalized concept layer needed for downstream chunking and indexing.
- `data/processed/esco/normalized/esco_relations.jsonl` is tracked because it is the normalized relation graph needed for downstream retrieval work.
- `data/processed/esco/manifests/esco_normalization_stats.json` is tracked because it records preprocessing provenance.

#### Step 2. Translate normalized concept text into Russian

```bash
python -m tooling.translation.translate_esco_to_russian
```

This writes:

- `data/processed/esco/bilingual/esco_concepts.en_ru.jsonl`
- `data/processed/esco/manifests/esco_translation_manifest.json`

Tracking policy for this step:

- `data/processed/esco/bilingual/esco_concepts.en_ru.jsonl` is tracked because it is a meaningful one-time academic output.
- `data/processed/esco/manifests/esco_translation_manifest.json` is tracked because it records translation provenance and run settings.

#### Step 3. Inspect the bilingual output manually

Review a sample of:

- occupations
- skills
- long descriptions
- multiline label fields

Do this before starting chunking or retrieval work.

### Performance Tuning

For this script, the main throughput knob is `--text-batch-size`.

Practical interpretation:

- `--text-batch-size` controls how many text fragments are translated together on the GPU.
- `--record-batch-size` controls how many ESCO concept records are flattened at a time so the script has enough text fragments to fill the text batches.
- `--num-beams 1` is the fastest deterministic decoding path in this workflow.
- `--compile` enables `torch.compile` on the model forward pass. This may improve throughput after warm-up, but the first batches can be slower.
- If `--compile --compile-mode reduce-overhead` is unstable on your workstation, try `--compile --compile-mode max-autotune-no-cudagraphs`.
- Length bucketing is enabled by default and sorts text fragments by approximate length before batching to reduce padding waste.

Recommended tuning order:

1. Increase `--text-batch-size` until throughput stops improving or you hit memory pressure.
2. Keep `--record-batch-size` high enough to feed those text batches, but do not treat it as the primary speed knob.
3. Keep `--num-beams 1` unless you have a quality reason to pay for slower decoding.
4. Try `--compile` after you have a stable batch configuration.

Example tuning command:

```bash
python -m tooling.translation.translate_esco_to_russian \
  --overwrite \
  --limit 250 \
  --text-batch-size 16 \
  --record-batch-size 4 \
  --num-beams 1 \
  --max-source-length 256 \
  --max-new-tokens 256
```

Example compile benchmark:

```bash
python -m tooling.translation.translate_esco_to_russian \
  --overwrite \
  --limit 250 \
  --text-batch-size 16 \
  --record-batch-size 4 \
  --num-beams 1 \
  --max-source-length 256 \
  --max-new-tokens 256 \
  --compile
```

Recommended full-run command for an RTX 4090 workstation:

```bash
python -m tooling.translation.translate_esco_to_russian \
  --text-batch-size 64 \
  --record-batch-size 8 \
  --num-beams 1 \
  --max-source-length 256 \
  --max-new-tokens 256
```

This is the current recommended non-compiled baseline because it uses the GPU
well without paying the compile and Triton autotune overhead of the compiled
path.

### Common Internal Format

The preprocessing workflow creates two artifact families:

1. concept records
2. relation records

#### Concept record shape

Concept records are normalized into a bilingual-ready format. English remains
canonical. Russian is added later under `translations.ru`.

Representative example:

```json
{
  "record_type": "concept",
  "dataset": "esco",
  "dataset_version": "1.2.1",
  "source_language": "en",
  "concept_kind": "occupation",
  "raw_concept_type": "Occupation",
  "concept_uri": "http://data.europa.eu/esco/occupation/...",
  "status": "released",
  "source_text": {
    "preferred_label": "technical director",
    "alt_labels": ["director of technical arts", "technical supervisor"],
    "hidden_labels": [],
    "description": "...",
    "definition": "...",
    "scope_note": "...",
    "regulated_profession_note": null
  },
  "translations": {
    "ru": {
      "preferred_label": "технический директор",
      "alt_labels": ["..."],
      "hidden_labels": [],
      "description": "...",
      "definition": "...",
      "scope_note": "...",
      "regulated_profession_note": null,
      "translation_meta": {
        "model_name": "facebook/nllb-200-3.3B",
        "source_language": "eng_Latn",
        "target_language": "rus_Cyrl",
        "translated_at": "..."
      }
    }
  },
  "classification": {
    "isco_group": "2654",
    "skill_type": null,
    "reuse_level": null,
    "code": null,
    "nace_code": null,
    "in_scheme": ["http://data.europa.eu/esco/concept-scheme/occupations"]
  },
  "audit": {
    "source_file": "occupations_en.csv",
    "modified_date": "...",
    "normalized_at": "..."
  }
}
```

#### Relation record shape

Relations stay language-neutral and URI-centered.

Representative example:

```json
{
  "record_type": "relation",
  "dataset": "esco",
  "dataset_version": "1.2.1",
  "relation_family": "occupation_skill",
  "relation_type": "essential",
  "source_uri": "http://data.europa.eu/esco/occupation/...",
  "source_kind": "occupation",
  "source_label_en": "technical director",
  "target_uri": "http://data.europa.eu/esco/skill/...",
  "target_kind": "skill_concept",
  "target_subtype": "knowledge",
  "target_label_en": "theatre techniques",
  "audit": {
    "source_file": "occupationSkillRelations_en.csv"
  }
}
```

### What Gets Translated

The translation script translates only user-facing concept text:

- `preferred_label`
- `alt_labels`
- `hidden_labels`
- `description`
- `definition`
- `scope_note`
- `regulated_profession_note`

### What Does Not Get Translated

The translation script does not translate:

- URIs
- concept identifiers
- relation rows as standalone truth
- graph structure
- classification codes
- audit metadata

### Why Relations Stay Language-Neutral

Relations are structural facts. They should stay stable and language-neutral.

Later app stages can join:

- relation records
- bilingual concept records

using the concept URI.

This gives us:

- one stable graph
- multiple display languages
- less duplication of structure
- less risk of translation drift in the graph

### Resumability And Useful Options

The translation script is resumable.

If the bilingual output file already exists, the script reads completed concept
URIs and skips those records on later runs.

If an older partial run wrote duplicate concept URIs into the bilingual output,
the script compacts that file before resuming so the tracked artifact stays
clean.

Useful commands:

```bash
python -m tooling.translation.translate_esco_to_russian --limit 100
python -m tooling.translation.translate_esco_to_russian --overwrite
python -m tooling.translation.translate_esco_to_russian --model-name facebook/nllb-200-3.3B
```

Useful behavior:

- `--limit` is for debugging or a short smoke test
- `--overwrite` deletes the previous bilingual output and starts over
- default batching is conservative and can be tuned later if GPU memory allows

### Verified Against The Current ESCO Export

The normalization step has already been run successfully against the real raw
English CSV export currently in this repository.

Observed normalized counts:

- `occupation = 3039`
- `skill_concept = 13939`
- `isco_group = 619`
- `skill_group = 640`
- `occupation_skill relations = 126051`
- `skill_skill relations = 5818`
- `broader relations = 24467`
- `duplicate concept rows removed = 25`

Manifest file:

- `data/processed/esco/manifests/esco_normalization_stats.json`

### What Happens After This Stage

Only after preprocessing and translation review are complete should the project
move into:

- chunk generation
- multilingual indexing
- embeddings
- reranking
- grounded generation
- live app integration

This directory is not the app pipeline. It is the one-time source preparation
stage.

### Related Repository Docs

- `docs/ESCO_PREPROCESSING.md`
- `docs/SETUP.md`
- `docs/STATUS.md`
