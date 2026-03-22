# ESCO Translation Tooling

## English

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

## Русский

### Для чего нужна эта директория

Эта директория содержит standalone tooling для one-time preprocessing исходных
данных ESCO.

Этот этап выполняется до application pipeline.

На этом этапе мы еще не:

- строим live retrieval pipeline
- создаем app-ready chunks
- считаем embeddings
- запускаем reranking
- обслуживаем web app

На этом этапе мы только:

1. читаем raw ESCO English CSV export
2. нормализуем его в единый внутренний формат
3. создаем производный русский translation layer
4. записываем двуязычные артефакты в `data/processed/esco/`

Выход этого tooling становится доверенным двуязычным source layer для
последующего application pipeline.

### Текущий ожидаемый вход

Для этого preprocessing stage ожидается English classification CSV export, а не
большой пакет Local API.

Текущая ожидаемая raw-директория:

- `data/raw/ESCO/ESCO_dataset_v1.2.1_classification_en_csv/`

Важные входные файлы:

- `occupations_en.csv`
- `skills_en.csv`
- `occupationSkillRelations_en.csv`
- `skillSkillRelations_en.csv`
- `broaderRelationsOccPillar_en.csv`
- `broaderRelationsSkillPillar_en.csv`
- `ISCOGroups_en.csv`
- `skillGroups_en.csv`

Если вы скачиваете ESCO специально для этого tooling, практический выбор такой:

1. `ESCO dataset`
2. `classification`
3. `en`
4. `csv`

Пакет Local API для этого preprocessing workflow не нужен.

### Почему мы сначала нормализуем, а потом переводим

Репозиторий должен сохранять исходный ESCO source text и identifiers.

Это означает:

- English source data остается каноническим.
- Русский хранится как производный layer.
- Relations остаются URI-first и language-neutral.
- Поздние этапы pipeline смогут связывать bilingual concept records и relation records по URI.

Это сохраняет:

- provenance
- точность цитирования
- воспроизводимость
- академическую добросовестность

### Почему ESCO URI важны

ESCO URI - это стабильный идентификатор concept.

Это важно, потому что:

- occupations и skills связаны с остальным ESCO graph через URI
- relation files указывают на concept URI, а не на translated labels
- позже приложение будет связывать bilingual concept text обратно с relation graph по URI

Без URI у проекта не было бы стабильного способа связать:

- English source text
- Russian translated text
- occupation-skill relations
- hierarchy relations

### Важное предупреждение по CSV

Эти ESCO CSV-файлы содержат quoted multiline cells.

Это часто встречается в полях:

- `altLabels`
- `description`
- `scopeNote`
- `inScheme`

Из-за этого raw line count не равен реальному числу records. Эти файлы нужно
обрабатывать полноценным CSV parser. Не используйте разбиение по строкам или
regex-хаки.

Текущий vendor CSV также содержит небольшое число duplicate concept rows с
одинаковым `conceptUri`. В этом dump такие duplicate rows отличаются только
полем `modifiedDate`. Normalizer схлопывает их по URI и сохраняет самую новую
source row.

### Структура tooling

- `normalize_esco_csv.py`
  Читает raw English ESCO CSV files и записывает нормализованные concept и
  relation JSONL artifacts.

- `translate_esco_to_russian.py`
  Читает нормализованные concept records и записывает производные русские
  переводы в bilingual JSONL artifact.

- `common.py`
  Общие helpers для CSV parsing, text cleanup и JSON/JSONL output.

- `paths.py`
  Общие input/output paths, используемые preprocessing tooling.

- `requirements.txt`
  Канонический набор зависимостей для standalone translation workflow под
  WSL2/Linux workstation, включая CUDA-enabled PyTorch baseline.

### Рекомендуемое окружение

Этот tooling ориентирован на ваш workstation workflow, а не на повседневную
student app-разработку.

Чистый и воспроизводимый путь - отдельное Conda-окружение в WSL2.

Рекомендуемое standalone tooling environment для workstation с NVIDIA GPU:

```bash
cd /mnt/e/Work-Repos-SiftVPN/CareerGuide
source ~/miniconda3/etc/profile.d/conda.sh

conda create -n careerguide-tools python=3.11 -y
conda activate careerguide-tools

python -m pip install --upgrade pip
python -m pip install -r tooling/translation/requirements.txt
```

Примечания:

- `tooling/translation/requirements.txt` теперь включает канонический GPU runtime baseline для этого one-time translation workflow.
- Зафиксированный baseline: PyTorch `2.6.0` из CUDA `12.4` wheel index.
- Это практический выбор ради воспроизводимости для WSL2 и мощной NVIDIA GPU, например RTX 4090.
- Translation script автоматически использует `float16`, когда доступна CUDA.

Если вы хотите переиспользовать уже существующее CUDA-ready Conda-окружение
вместо нового, сначала проверьте GPU:

```bash
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CUDA not available')"
```

Если эта команда показывает рабочее CUDA device, можно оставить текущее
окружение и установить только non-torch extras:

```bash
python -m pip install --upgrade pip
python -m pip install "accelerate>=1.2,<2" "safetensors>=0.4,<1" "sentencepiece>=0.2,<1" "transformers>=4.48,<5" "tqdm>=4.66,<5"
```

Для этого repo authoritative clean-install path остается отдельное окружение
`careerguide-tools`, указанное выше.

### Проверка окружения

После установки проверьте, что PyTorch видит GPU:

```bash
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CUDA not available')"
```

Ожидаемый результат на рабочем workstation setup:

- напечатанная версия torch
- `True` для `torch.cuda.is_available()`
- имя вашей GPU, например `NVIDIA GeForce RTX 4090`

### Рекомендуемая модель перевода

Модель перевода по умолчанию в script:

- `facebook/nllb-200-3.3B`

Текущие language codes по умолчанию:

- source: `eng_Latn`
- target: `rus_Cyrl`

Почему именно она:

- это translation model, а не general chat model
- она подходит для one-time preprocessing на сильной workstation GPU
- это более качественный выбор для English-to-Russian, чем меньшая distilled-версия

Эта модель используется только для preprocessing. Это не runtime generator
приложения.

### Быстрый старт

#### Шаг 1. Нормализовать raw ESCO CSV export

```bash
python -m tooling.translation.normalize_esco_csv
```

Скрипт читает из:

- `data/raw/ESCO/ESCO_dataset_v1.2.1_classification_en_csv/`

Скрипт записывает:

- `data/processed/esco/normalized/esco_concepts.en.jsonl`
- `data/processed/esco/normalized/esco_relations.jsonl`
- `data/processed/esco/manifests/esco_normalization_stats.json`

Политика отслеживания для этого шага:

- `data/raw/ESCO/` остается игнорируемой, потому что это vendor download.
- `data/processed/esco/normalized/esco_concepts.en.jsonl` отслеживается, потому что это нормализованный слой concept, необходимый для downstream chunking и indexing.
- `data/processed/esco/normalized/esco_relations.jsonl` отслеживается, потому что это нормализованный relation graph, необходимый для downstream retrieval-работы.
- `data/processed/esco/manifests/esco_normalization_stats.json` отслеживается, потому что фиксирует provenance preprocessing-процесса.

#### Шаг 2. Перевести нормализованный concept text на русский

```bash
python -m tooling.translation.translate_esco_to_russian
```

Скрипт записывает:

- `data/processed/esco/bilingual/esco_concepts.en_ru.jsonl`
- `data/processed/esco/manifests/esco_translation_manifest.json`

Политика отслеживания для этого шага:

- `data/processed/esco/bilingual/esco_concepts.en_ru.jsonl` отслеживается, потому что это значимый one-time академический результат.
- `data/processed/esco/manifests/esco_translation_manifest.json` отслеживается, потому что фиксирует provenance перевода и параметры запуска.

#### Шаг 3. Вручную проверить двуязычный output

Проверьте выборку:

- occupations
- skills
- длинные descriptions
- multiline label fields

Сделайте это до начала chunking и retrieval work.

### Настройка производительности

Для этого script основной throughput knob - это `--text-batch-size`.

Практический смысл:

- `--text-batch-size` управляет тем, сколько text fragments переводятся вместе на GPU.
- `--record-batch-size` управляет тем, сколько ESCO concept records разворачиваются за раз, чтобы у script было достаточно text fragments для заполнения text batches.
- `--num-beams 1` является самым быстрым deterministic decoding path в этом workflow.
- `--compile` включает `torch.compile` для model forward pass. Это может повысить throughput после warm-up, но первые batches могут быть медленнее.
- Если `--compile --compile-mode reduce-overhead` ведет себя нестабильно на вашей workstation, попробуйте `--compile --compile-mode max-autotune-no-cudagraphs`.
- Length bucketing включен по умолчанию и сортирует text fragments по приблизительной длине перед batching, чтобы уменьшить padding waste.

Рекомендуемый порядок настройки:

1. Увеличивайте `--text-batch-size`, пока throughput растет и не появляется memory pressure.
2. Держите `--record-batch-size` достаточно высоким, чтобы заполнять text batches, но не считайте его главным speed knob.
3. Держите `--num-beams 1`, если у вас нет причин по качеству платить за более медленный decoding.
4. Пробуйте `--compile` после того, как у вас уже есть стабильная batch-конфигурация.

Пример tuning command:

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

Пример compile benchmark:

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

Рекомендуемая full-run команда для workstation с RTX 4090:

```bash
python -m tooling.translation.translate_esco_to_russian \
  --text-batch-size 64 \
  --record-batch-size 8 \
  --num-beams 1 \
  --max-source-length 256 \
  --max-new-tokens 256
```

Это текущий рекомендуемый non-compiled baseline, потому что он хорошо
использует GPU без compile и Triton autotune overhead, который был виден в
compiled path.

### Общий внутренний формат

Preprocessing workflow создает два семейства артефактов:

1. concept records
2. relation records

#### Формат concept record

Concept records нормализуются в формат, готовый к двуязычному использованию.
English остается каноническим. Русский позже добавляется в `translations.ru`.

Показательный пример:

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

#### Формат relation record

Relations остаются language-neutral и URI-centered.

Показательный пример:

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

### Что переводится

Translation script переводит только user-facing concept text:

- `preferred_label`
- `alt_labels`
- `hidden_labels`
- `description`
- `definition`
- `scope_note`
- `regulated_profession_note`

### Что не переводится

Translation script не переводит:

- URI
- concept identifiers
- relation rows как самостоятельный источник истины
- graph structure
- classification codes
- audit metadata

### Почему relations остаются language-neutral

Relations являются структурными фактами. Они должны оставаться стабильными и
language-neutral.

Поздние app stages смогут связывать:

- relation records
- bilingual concept records

по concept URI.

Это дает:

- один стабильный graph
- несколько display languages
- меньше дублирования структуры
- меньший риск translation drift в graph

### Возобновляемость и полезные опции

Translation script является resumable.

Если bilingual output file уже существует, script читает уже завершенные
concept URI и пропускает их в следующих запусках.

Если более ранний partial run записал duplicate concept URI в bilingual output,
script уплотняет этот файл перед возобновлением, чтобы отслеживаемый артефакт
оставался чистым.

Полезные команды:

```bash
python -m tooling.translation.translate_esco_to_russian --limit 100
python -m tooling.translation.translate_esco_to_russian --overwrite
python -m tooling.translation.translate_esco_to_russian --model-name facebook/nllb-200-3.3B
```

Полезное поведение:

- `--limit` нужен для debugging или короткого smoke test
- `--overwrite` удаляет предыдущий bilingual output и запускает полный прогон заново
- batching по умолчанию консервативный и может быть позже настроен под объем GPU memory

### Что уже проверено на текущем ESCO export

Шаг нормализации уже успешно выполнен на реальном raw English CSV export,
который сейчас лежит в этом репозитории.

Полученные normalized counts:

- `occupation = 3039`
- `skill_concept = 13939`
- `isco_group = 619`
- `skill_group = 640`
- `occupation_skill relations = 126051`
- `skill_skill relations = 5818`
- `broader relations = 24467`
- `удалено duplicate concept rows = 25`

Файл manifest:

- `data/processed/esco/manifests/esco_normalization_stats.json`

### Что происходит после этого этапа

Только после завершения preprocessing и проверки перевода проект должен
переходить к:

- chunk generation
- multilingual indexing
- embeddings
- reranking
- grounded generation
- live app integration

Эта директория не является app pipeline. Это one-time stage подготовки source
данных.

### Связанные документы репозитория

- `docs/ESCO_PREPROCESSING.md`
- `docs/SETUP.md`
- `docs/STATUS.md`
