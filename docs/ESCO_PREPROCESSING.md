# ESCO Preprocessing And Translation

## English

### Purpose

This document defines the one-time preprocessing workflow for the ESCO source data.

This workflow happens **before** the application pipeline. The goal here is not
yet to serve the app directly. The goal is to convert raw ESCO source files into
a stable, bilingual-ready internal format that the app pipeline can later index,
chunk, embed, rerank, and cite.

### Current Input

The current raw source is the English CSV classification dump:

- `data/raw/ESCO/ESCO_dataset_v1.2.1_classification_en_csv/`

The most important files in that dump are:

- `occupations_en.csv`
- `skills_en.csv`
- `occupationSkillRelations_en.csv`
- `skillSkillRelations_en.csv`
- `broaderRelationsOccPillar_en.csv`
- `broaderRelationsSkillPillar_en.csv`
- `ISCOGroups_en.csv`
- `skillGroups_en.csv`

### Important CSV Parsing Note

ESCO CSV files contain quoted multiline cells, especially in fields such as:

- `altLabels`
- `description`
- `scopeNote`
- `inScheme`

That means raw line counts are not the same as record counts. The files must be
parsed with a real CSV parser, not line splitting.

The current ESCO English CSV dump also contains a small number of duplicate
concept rows with the same `conceptUri`. In the current vendor dump these
duplicates differ only by `modifiedDate`. The normalizer collapses those rows by
URI and keeps the latest source row.

### Why We Normalize Before Translation

The repository must preserve the original source text and source identifiers.

That means:

- English source fields remain canonical.
- Russian text is added as a derived layer.
- Relation records remain concept-URI-first and language-neutral.
- Later app-pipeline stages can choose English or Russian labels by joining on concept URIs.

The URI is the stable ESCO identifier that lets the project join:

- bilingual concept text
- occupation-skill relations
- hierarchy relations
- source provenance

This protects provenance, citations, and academic honesty.

### Common Internal Format

The preprocessing workflow creates two main artifact families:

1. concept records
2. relation records

#### Concept record shape

Each concept record is normalized into a common format that can support both
English and Russian later.

Representative shape:

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
      "preferred_label": "...",
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

Relations stay URI-centered so the same graph can support multiple display
languages later.

Representative shape:

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

### Output Layout

The preprocessing tooling writes to:

- `data/processed/esco/normalized/esco_concepts.en.jsonl`
- `data/processed/esco/normalized/esco_relations.jsonl`
- `data/processed/esco/manifests/esco_normalization_stats.json`
- `data/processed/esco/bilingual/esco_concepts.en_ru.jsonl`
- `data/processed/esco/manifests/esco_translation_manifest.json`

Tracking policy for these artifacts:

- `data/raw/ESCO/` remains ignored because it is a vendor download.
- `data/processed/esco/normalized/esco_concepts.en.jsonl` should be tracked because it is the normalized concept layer used by downstream chunking and indexing.
- `data/processed/esco/normalized/esco_relations.jsonl` should be tracked because it is the normalized ESCO graph needed to continue retrieval work without rerunning preprocessing.
- `data/processed/esco/bilingual/esco_concepts.en_ru.jsonl` should be tracked because it is a meaningful one-time academic output.
- `data/processed/esco/manifests/*.json` should be tracked because they preserve preprocessing provenance.

### Translation Method

The translation workflow is designed as a one-time preprocessing step.

Current planned model:

- `facebook/nllb-200-3.3B`

Translation direction:

- source: `eng_Latn`
- target: `rus_Cyrl`

Key choices:

- deterministic beam search instead of sampling
- source English fields remain unchanged
- Russian output is written into `translations.ru`
- empty fields are not translated
- relation files are not directly translated because the relation graph should stay language-neutral
- text fragments are length-bucketed before translation batching to reduce padding waste
- optional `torch.compile` support exists for translation benchmarking on workstation hardware

### What We Translate

For each concept record, the tooling translates:

- `preferred_label`
- `alt_labels`
- `hidden_labels`
- `description`
- `definition`
- `scope_note`
- `regulated_profession_note`

### What We Do Not Translate

- URIs
- concept ids
- relation files as standalone truth
- structural metadata
- classification codes
- audit fields

### Why Relations Stay Language-Neutral

The app should later join relation records to bilingual concept records by URI.

This gives us:

- one stable graph
- two or more display languages
- no duplication of graph structure per language
- less risk of translation drift in structural data

### Operational Sequence

The one-time preprocessing flow is:

1. place raw ESCO English CSV under `data/raw/ESCO/...`
2. run `python -m tooling.translation.normalize_esco_csv`
3. inspect the normalization stats
4. run `python -m tooling.translation.translate_esco_to_russian`
5. review a sample of translated concept records manually
6. only after that, start app-pipeline work such as chunking, indexing, embedding, and retrieval evaluation

### Important Notes

- This preprocessing stage is distinct from the application pipeline.
- We are not yet building retrieval chunks for the live app here.
- We are first building a stable bilingual source layer that later app stages can trust.
- Raw vendor ESCO data remains ignored by git.
- The normalized ESCO concept and relation JSONL artifacts are intended to be tracked by git.
- The bilingual translated concept corpus and preprocessing manifests are intended to be tracked by git.
- For translation throughput, `text-batch-size` is the primary tuning knob; `record-batch-size` mainly helps keep the text batches filled.
- Current recommended RTX 4090 full-run command: `python -m tooling.translation.translate_esco_to_russian --text-batch-size 64 --record-batch-size 8 --num-beams 1 --max-source-length 256 --max-new-tokens 256`

## Русский

### Назначение

Этот документ определяет one-time preprocessing workflow для исходных данных ESCO.

Этот workflow выполняется **до** application pipeline. На этом этапе цель еще не
в том, чтобы напрямую обслуживать приложение. Цель состоит в том, чтобы
преобразовать raw ESCO source files в стабильный внутренний формат, готовый к
двуязычной работе, который позже application pipeline сможет индексировать,
chunk-ить, embed-ить, rerank-ить и цитировать.

### Текущий вход

Текущий raw source - это English CSV classification dump:

- `data/raw/ESCO/ESCO_dataset_v1.2.1_classification_en_csv/`

Наиболее важные файлы в этом наборе:

- `occupations_en.csv`
- `skills_en.csv`
- `occupationSkillRelations_en.csv`
- `skillSkillRelations_en.csv`
- `broaderRelationsOccPillar_en.csv`
- `broaderRelationsSkillPillar_en.csv`
- `ISCOGroups_en.csv`
- `skillGroups_en.csv`

### Важное замечание по CSV parsing

ESCO CSV-файлы содержат quoted multiline cells, особенно в таких полях, как:

- `altLabels`
- `description`
- `scopeNote`
- `inScheme`

Это означает, что raw line counts не совпадают с числом records. Эти файлы нужно
разбирать полноценным CSV parser, а не разбиением по строкам.

Текущий English CSV dump ESCO также содержит небольшое число duplicate concept
rows с одинаковым `conceptUri`. В текущем vendor dump эти duplicate rows
отличаются только полем `modifiedDate`. Normalizer схлопывает такие строки по
URI и сохраняет самую новую source row.

### Почему мы нормализуем до перевода

Репозиторий должен сохранять исходный source text и source identifiers.

Это означает:

- английские source-поля остаются каноническими
- русский текст добавляется как производный слой
- relation records остаются concept-URI-first и language-neutral
- более поздние этапы app pipeline смогут выбирать английские или русские labels через join по concept URI

URI является стабильным идентификатором ESCO, который позволяет проекту
связывать:

- bilingual concept text
- occupation-skill relations
- hierarchy relations
- source provenance

Это защищает provenance, citations и академическую добросовестность.

### Общий внутренний формат

Preprocessing workflow создает два основных семейства артефактов:

1. concept records
2. relation records

#### Форма concept record

Каждая concept record нормализуется в общий формат, который позже сможет
поддерживать и английский, и русский языки.

#### Форма relation record

Relations остаются URI-центричными, чтобы один и тот же граф мог позже
поддерживать несколько display-языков.

### Выходной layout

Preprocessing tooling пишет в:

- `data/processed/esco/normalized/esco_concepts.en.jsonl`
- `data/processed/esco/normalized/esco_relations.jsonl`
- `data/processed/esco/manifests/esco_normalization_stats.json`
- `data/processed/esco/bilingual/esco_concepts.en_ru.jsonl`
- `data/processed/esco/manifests/esco_translation_manifest.json`

Политика отслеживания для этих артефактов:

- `data/raw/ESCO/` остается игнорируемой, потому что это vendor download.
- `data/processed/esco/normalized/esco_concepts.en.jsonl` следует отслеживать, потому что это нормализованный слой concept, используемый downstream при chunking и indexing.
- `data/processed/esco/normalized/esco_relations.jsonl` следует отслеживать, потому что это нормализованный ESCO graph, необходимый для продолжения retrieval-работы без повторного запуска preprocessing.
- `data/processed/esco/bilingual/esco_concepts.en_ru.jsonl` следует отслеживать, потому что это значимый one-time академический результат.
- `data/processed/esco/manifests/*.json` следует отслеживать, потому что эти файлы сохраняют provenance preprocessing-процесса.

### Метод перевода

Translation workflow спроектирован как one-time preprocessing step.

Текущая планируемая модель:

- `facebook/nllb-200-3.3B`

Направление перевода:

- source: `eng_Latn`
- target: `rus_Cyrl`

Ключевые решения:

- deterministic beam search вместо sampling
- исходные английские поля остаются без изменений
- русский вывод записывается в `translations.ru`
- пустые поля не переводятся
- relation-файлы напрямую не переводятся, потому что relation graph должен оставаться language-neutral
- text fragments группируются по приблизительной длине перед translation batching, чтобы уменьшить padding waste
- существует optional-поддержка `torch.compile` для translation benchmarking на workstation hardware

### Что мы переводим

Для каждой concept record tooling переводит:

- `preferred_label`
- `alt_labels`
- `hidden_labels`
- `description`
- `definition`
- `scope_note`
- `regulated_profession_note`

### Что мы не переводим

- URI
- concept ids
- relation files как самостоятельный источник истины
- structural metadata
- classification codes
- audit fields

### Почему relations остаются language-neutral

Приложение позже должно делать join relation records к bilingual concept records по URI.

Это дает:

- один стабильный граф
- два и более display-языка
- отсутствие дублирования графовой структуры на каждый язык
- меньший риск translation drift в структурных данных

### Последовательность работы

One-time preprocessing flow выглядит так:

1. поместить raw ESCO English CSV в `data/raw/ESCO/...`
2. запустить `python -m tooling.translation.normalize_esco_csv`
3. проверить normalization stats
4. запустить `python -m tooling.translation.translate_esco_to_russian`
5. вручную проверить выборку translated concept records
6. только после этого переходить к app-pipeline work, таким как chunking, indexing, embedding и retrieval evaluation

### Важные замечания

- Этот preprocessing stage отделен от application pipeline.
- На этом этапе мы еще не строим retrieval chunks для live app.
- Сначала мы строим стабильный bilingual source layer, которому смогут доверять последующие стадии.
- Raw vendor ESCO data остается игнорируемым git.
- Нормализованный промежуточный ESCO JSONL остается игнорируемым git.
- Двуязычный translated concept corpus и preprocessing manifests предполагается отслеживать в git.
- Для translation throughput главным tuning knob является `text-batch-size`; `record-batch-size` в основном помогает держать text batches заполненными.
- Текущая рекомендуемая full-run команда для RTX 4090: `python -m tooling.translation.translate_esco_to_russian --text-batch-size 64 --record-batch-size 8 --num-beams 1 --max-source-length 256 --max-new-tokens 256`
