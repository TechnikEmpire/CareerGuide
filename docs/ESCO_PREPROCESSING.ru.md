# ESCO Preprocessing And Translation

### Назначение

В этом документе описан порядок однократной предварительной обработки исходных данных перечня Европейских навыков, компетенций, квалификаций и профессий.

Этот рабочий процесс выполняется **до** пайплайна разработки приложения. На этом этапе цель еще не
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
