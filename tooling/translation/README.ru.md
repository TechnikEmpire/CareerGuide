# ESCO Translation Tooling

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
