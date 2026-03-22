# Project Status

Last updated: 2026-03-22

Последнее обновление: 2026-03-22

## English

### Current Phase

Foundational scaffold with repo governance, backend skeleton, bilingual documentation, and initial tests.

### What Is Already Done

- Bilingual authoritative repo documentation is in place.
- Canonical decision tracking is in place.
- Local setup instructions exist for WSL, Windows, and macOS.
- A Python-first backend scaffold exists with FastAPI routing and explicit service boundaries.
- The initial retrieval scaffold exists.
- The initial Hopfield-style associative-read scaffold exists.
- Bilingual evaluation scenarios exist.
- Standalone ESCO preprocessing and translation tooling now exists under `tooling/translation/`.
- The ESCO English CSV classification dump has been inspected and normalized into the repository's common bilingual-ready concept and relation format.
- The one-time ESCO English-to-Russian translation run has been completed and written to the tracked bilingual corpus.
- ESCO artifact tracking policy is now defined: raw vendor data stays ignored, while the normalized concept layer, normalized relation graph, bilingual translated corpus, and preprocessing manifests are tracked deliverables.
- The ESCO translation script now supports length-bucketing for translation batches and an optional `torch.compile` path for workstation-side throughput tuning.
- ESCO preprocessing now treats `conceptUri` as the canonical concept key and collapses duplicate vendor concept rows by keeping the latest `modifiedDate`.
- The first backend tests are passing in the `careerguide` Conda environment.

### What Is In Progress

- Moving from scaffold retrieval to real corpus-backed retrieval
- Aligning the production retrieval stack with Russian-first requirements
- Moving from stub generation to real `llama.cpp` integration
- Moving from placeholder evaluation to baseline-comparison evaluation

### What Is Not Done Yet

- SQLite-backed chunk and embedding index
- Production embedding and reranking stack
- Persistent memory storage
- Full safety policy implementation
- Full experiment harness and report-ready result exports

### Immediate Next Steps

1. Move from the tracked bilingual ESCO source layer into chunk generation for the app pipeline.
2. Build the first SQLite-backed lexical and metadata index over the normalized concept and relation artifacts.
3. Wire multilingual embeddings and reranking against the processed ESCO corpus.
4. Move from bilingual source preprocessing into real retrieval-backed generation.

### Current Risks and Notes

- The pinned generator model supports Russian. The production retrieval plan must therefore use multilingual retrieval components as well, rather than English-only embedding or reranking models.
- ESCO CSV files contain multiline quoted fields, so raw line counts are not reliable record counts. Parsing must use a proper CSV reader.
- The current retrieval and generation behavior is still scaffold logic, not the final academic system.
- FastAPI currently raises a deprecation warning for `on_event`; this is not blocking, but it should be cleaned up when the app wiring matures.

### Latest Verification

- `python -m pytest backend/tests -q`
- Result: `5 passed`
- `python -m tooling.translation.normalize_esco_csv`
- Result: normalized ESCO output written successfully
- Parsed deduped concept counts: `occupation=3039`, `skill_concept=13939`, `isco_group=619`, `skill_group=640`
- Duplicate vendor concept rows removed during normalization: `25`
- Final tracked ESCO outputs: normalized concepts=`18237`, normalized relations=`156336`, bilingual translated concepts=`18237`
- Current recommended RTX 4090 translation baseline: `python -m tooling.translation.translate_esco_to_russian --text-batch-size 64 --record-batch-size 8 --num-beams 1 --max-source-length 256 --max-new-tokens 256`

## Русский

### Текущая фаза

Базовый scaffold с governance-документацией репозитория, skeleton backend, двуязычной документацией и первыми тестами.

### Что уже сделано

- Создана двуязычная authoritative-документация репозитория.
- Настроено каноническое отслеживание решений.
- Есть инструкции по локальной настройке для WSL, Windows и macOS.
- Существует Python-first backend scaffold с FastAPI-routing и явными границами сервисов.
- Существует начальный retrieval-scaffold.
- Существует начальный Hopfield-style associative-read scaffold.
- Существуют двуязычные evaluation-сценарии.
- Теперь существует standalone tooling для preprocessing и перевода ESCO в `tooling/translation/`.
- Английский ESCO CSV classification dump был проверен и нормализован во внутренний common bilingual-ready format для concept и relation records.
- One-time ESCO translation run с английского на русский завершен и записан в отслеживаемый двуязычный corpus.
- Теперь определена политика отслеживания ESCO-артефактов: raw vendor data остается игнорируемой, а нормализованный слой concept, нормализованный relation graph, двуязычный translated corpus и preprocessing manifests считаются отслеживаемыми deliverables.
- Translation script для ESCO теперь поддерживает length-bucketing для translation batches и optional-путь `torch.compile` для настройки throughput на workstation.
- ESCO preprocessing теперь рассматривает `conceptUri` как канонический concept key и схлопывает duplicate vendor concept rows, сохраняя самую новую `modifiedDate`.
- Первые backend-тесты проходят в Conda-окружении `careerguide`.

### Что сейчас в работе

- Переход от scaffold-retrieval к реальному retrieval на основе корпуса
- Согласование production retrieval stack с требованием Russian-first
- Переход от stub-generation к реальной интеграции `llama.cpp`
- Переход от placeholder-evaluation к сравнению baseline-режимов

### Что еще не сделано

- SQLite-backed индекс chunk-ов и embeddings
- Production-стек для embeddings и reranking
- Persistent storage для памяти
- Полноценная реализация safety policy
- Полноценный experiment harness и экспорт результатов в report-ready формате

### Ближайшие шаги

1. Перейти от отслеживаемого двуязычного ESCO source layer к генерации chunk-ов для app pipeline.
2. Построить первый SQLite-backed lexical и metadata index поверх нормализованных concept и relation artifacts.
3. Подключить multilingual embeddings и reranking к обработанному ESCO corpus.
4. Перейти от bilingual source preprocessing к реальной retrieval-backed generation.

### Текущие риски и заметки

- Зафиксированная модель-генератор поддерживает русский язык. Поэтому production retrieval plan тоже должен использовать multilingual-компоненты, а не English-only embedding или reranking модели.
- ESCO CSV-файлы содержат multiline quoted fields, поэтому raw line counts не являются надежными record counts. Для разбора нужен полноценный CSV parser.
- Текущее поведение retrieval и generation пока является scaffold-логикой, а не финальной академической системой.
- FastAPI сейчас выдает deprecation warning для `on_event`; это не блокирует работу, но должно быть приведено в порядок по мере взросления app wiring.

### Последняя проверка

- `python -m pytest backend/tests -q`
- Результат: `5 passed`
- `python -m tooling.translation.normalize_esco_csv`
- Результат: нормализованный ESCO output успешно записан
- Parsed deduped concept counts: `occupation=3039`, `skill_concept=13939`, `isco_group=619`, `skill_group=640`
- Во время normalization удалено duplicate vendor concept rows: `25`
- Финальные отслеживаемые ESCO outputs: normalized concepts=`18237`, normalized relations=`156336`, bilingual translated concepts=`18237`
- Текущий рекомендуемый RTX 4090 baseline для перевода: `python -m tooling.translation.translate_esco_to_russian --text-batch-size 64 --record-batch-size 8 --num-beams 1 --max-source-length 256 --max-new-tokens 256`
