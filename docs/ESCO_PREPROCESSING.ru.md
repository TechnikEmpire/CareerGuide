# ESCO Preprocessing And Translation

### Назначение

В этом документе описан порядок однократной предварительной обработки исходных данных перечня Европейских навыков, компетенций, квалификаций и профессий.

Этот рабочий процесс выполняется **до** пайплайна разработки приложения. На этом этапе цель еще не состоит в том, чтобы напрямую обслуживать приложение. Цель состоит в том, чтобы
преобразовать сырые данные ESCO (Европейских навыков, компетенций, квалификаций и профессий) перевести в формат, готовый к работе на 2 языках, который далее будет использован для индексации,
чанков, эмбедингов, рангов и как библиотеку с данными.

### Текущий вход

Текущий сырой источник данных - это документы на английском языке в формате CSV:

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

### Важное замечание по парсингу CSV

ESCO CSV-файлы содержат в себе заключенные в ковычки слова и их сочетания, например:

- `altLabels`
- `description`
- `scopeNote`
- `inScheme`

Это означает, что количество строк в исходном виде не совпадает с количеством записей. Файлы необходимо анализировать с помощью CSV-парсера, а не путем разделения на строки.

Текущий ESCO CSV-файл на английском также содержит небольшое число также содержится небольшое количество повторяющихся строк с одинаковым `conceptUri`. В текущем наборе данных эти повторения
отличаются только полем `modifiedDate`. Нормалайзер сворачивает такие строки по URI и сохраняет самую новую исходную строку.

### Почему мы нормализуем до перевода

В репозитории необходимо сохранить исходный текст и идентификаторы источников.

Это означает:

- английские источники данных остаются каноническими
- русский текст добавляется как производный слой
- записи связей остаются с приоритетом к URI и лингвистически нейтральными
- на дальнейших этапах разработки приложения можно выбирать английские или русские метки через join по URI

URI является стабильным идентификатором ESCO, который позволяет проекту связывать:

- двуязычный текст
- связи между профессией и навыками
- иерархию связей
- источник происхождения данных

Это обеспечивает защиту происхождения материалов, цитирования и академической точность.

### Общий внутренний формат

Процесс предварительной обработки создает две основные группы артефактов:

1. записи концепций
2. записи отношений

#### Форма записи концепций

Каждая запись концепции нормализована в общий формат, который в дальнейшем будет поддерживать как английский, так и русский языки.

#### Форма записи отношений

Отношения остаются URI-центричными, чтобы один и тот же граф мог позже
поддерживать несколько языков.

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
