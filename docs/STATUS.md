# Project Status

Last updated: 2026-03-22

Последнее обновление: 2026-03-22

## English

### Current Phase

Foundational scaffold with repo governance, tracked ESCO source artifacts, and a Qwen3-targeted FAISS-backed dense retrieval path.

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
- The retrieval pipeline no longer depends on hard-coded demo chunks. It now uses a FAISS HNSW dense index built from a SQLite-persisted ESCO chunk store.
- The production retrieval defaults now point at `Qwen/Qwen3-Embedding-0.6B` for dense embeddings and `Qwen/Qwen3-Reranker-0.6B` for reranking.
- The planned generator default is now `Qwen/Qwen3-0.6B` via `llama.cpp`, replacing the older Qwen2.5 pin.
- The ESCO translation script now supports length-bucketing for translation batches and an optional `torch.compile` path for workstation-side throughput tuning.
- ESCO preprocessing now treats `conceptUri` as the canonical concept key and collapses duplicate vendor concept rows by keeping the latest `modifiedDate`.
- The first backend tests are passing in the `careerguide` Conda environment.

### What Is In Progress

- Adding explicit FAISS index rebuild and refresh workflow instead of relying on first-query materialization
- Moving from stub generation to real `llama.cpp` integration
- Moving from placeholder evaluation to baseline-comparison evaluation

### What Is Not Done Yet

- Full end-to-end runtime validation of the Qwen3 retrieval models on a real indexed corpus
- Full end-to-end runtime validation of the Qwen3 0.6B generator path through `llama.cpp`
- Persistent memory storage
- Full safety policy implementation
- Full experiment harness and report-ready result exports

### Immediate Next Steps

1. Add an explicit corpus-build or index-refresh command instead of seeding the persisted retrieval store lazily on first query.
2. Benchmark the Qwen3 embedding and reranking path on the real ESCO index and tune candidate-pool settings.
3. Move from the current FAISS-backed retrieval context into real retrieval-backed generation through the pinned `Qwen/Qwen3-0.6B` runtime.
4. Add persistent memory storage and stronger evaluation traces.

### Current Risks and Notes

- The pinned generator model now also sits on the Qwen3 family, alongside the retrieval encoder and reranker. The remaining risk is runtime validation and tuning, not cross-family mismatch.
- ESCO CSV files contain multiline quoted fields, so raw line counts are not reliable record counts. Parsing must use a proper CSV reader.
- The tests still force deterministic retrieval providers to keep smoke runs fast and independent of model downloads. Production defaults now point at Qwen3, so runtime model fetches happen outside the smoke-test path.
- The current generation behavior is still scaffold logic, not the final academic system.
- FastAPI currently raises a deprecation warning for `on_event`; this is not blocking, but it should be cleaned up when the app wiring matures.

### Latest Verification

- `python -m pytest backend/tests -q`
- Result: `5 passed`
- `python -m tooling.translation.normalize_esco_csv`
- Result: normalized ESCO output written successfully
- Parsed deduped concept counts: `occupation=3039`, `skill_concept=13939`, `isco_group=619`, `skill_group=640`
- Duplicate vendor concept rows removed during normalization: `25`
- Final tracked ESCO outputs: normalized concepts=`18237`, normalized relations=`156336`, bilingual translated concepts=`18237`
- Retrieval backend: SQLite-persisted ESCO chunks plus FAISS HNSW dense ANN search
- Production retrieval-model defaults: `Qwen/Qwen3-Embedding-0.6B` and `Qwen/Qwen3-Reranker-0.6B`
- Planned generator default: `Qwen/Qwen3-0.6B` via `Qwen/Qwen3-0.6B-GGUF:Q8_0`
- `python -m pytest backend/tests -q`
- Result after switching retrieval onto the FAISS HNSW backend: `5 passed`
- Current recommended RTX 4090 translation baseline: `python -m tooling.translation.translate_esco_to_russian --text-batch-size 64 --record-batch-size 8 --num-beams 1 --max-source-length 256 --max-new-tokens 256`

## Русский

### Текущая фаза

Базовый scaffold с governance-документацией репозитория, отслеживаемыми ESCO source artifacts и Qwen3-ориентированным FAISS-backed dense retrieval path.

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
- Retrieval pipeline больше не зависит от hard-coded demo chunks. Теперь он использует FAISS HNSW dense index, построенный из SQLite-persisted ESCO chunk store.
- Production-default для retrieval теперь указывает на `Qwen/Qwen3-Embedding-0.6B` для dense embeddings и `Qwen/Qwen3-Reranker-0.6B` для reranking.
- Планируемый generator-default теперь - `Qwen/Qwen3-0.6B` через `llama.cpp`, вместо более старого pin на Qwen2.5.
- Translation script для ESCO теперь поддерживает length-bucketing для translation batches и optional-путь `torch.compile` для настройки throughput на workstation.
- ESCO preprocessing теперь рассматривает `conceptUri` как канонический concept key и схлопывает duplicate vendor concept rows, сохраняя самую новую `modifiedDate`.
- Первые backend-тесты проходят в Conda-окружении `careerguide`.

### Что сейчас в работе

- Добавление явного corpus-build/index-refresh workflow вместо ленивой материализации persisted retrieval store при первом запросе
- Переход от stub-generation к реальной интеграции `llama.cpp`
- Переход от placeholder-evaluation к сравнению baseline-режимов

### Что еще не сделано

- Полная end-to-end runtime-валидация retrieval-моделей Qwen3 на реальном indexed corpus
- Полная end-to-end runtime-валидация генератора `Qwen/Qwen3-0.6B` через `llama.cpp`
- Persistent storage для памяти
- Полноценная реализация safety policy
- Полноценный experiment harness и экспорт результатов в report-ready формате

### Ближайшие шаги

1. Добавить явную команду corpus-build/index-refresh вместо ленивого наполнения persisted retrieval store при первом запросе.
2. Замерить и настроить путь Qwen3 embeddings + reranking на реальном ESCO index.
3. Перейти от текущего FAISS-backed retrieval context к реальной retrieval-backed generation через зафиксированный runtime `Qwen/Qwen3-0.6B`.
4. Добавить persistent storage для памяти и более сильные evaluation traces.

### Текущие риски и заметки

- Зафиксированная модель-генератор теперь тоже относится к семейству Qwen3, как и retrieval stack. Основной оставшийся риск связан не с несовпадением семейств моделей, а с runtime-валидацией и настройкой.
- ESCO CSV-файлы содержат multiline quoted fields, поэтому raw line counts не являются надежными record counts. Для разбора нужен полноценный CSV parser.
- Тесты по-прежнему принудительно используют deterministic retrieval providers, чтобы smoke-run оставался быстрым и не требовал загрузки моделей. Production-default при этом уже указывает на Qwen3.
- Текущее поведение generation пока является scaffold-логикой, а не финальной академической системой.
- FastAPI сейчас выдает deprecation warning для `on_event`; это не блокирует работу, но должно быть приведено в порядок по мере взросления app wiring.

### Последняя проверка

- `python -m pytest backend/tests -q`
- Результат: `5 passed`
- `python -m tooling.translation.normalize_esco_csv`
- Результат: нормализованный ESCO output успешно записан
- Parsed deduped concept counts: `occupation=3039`, `skill_concept=13939`, `isco_group=619`, `skill_group=640`
- Во время normalization удалено duplicate vendor concept rows: `25`
- Финальные отслеживаемые ESCO outputs: normalized concepts=`18237`, normalized relations=`156336`, bilingual translated concepts=`18237`
- Retrieval backend: SQLite-persisted ESCO chunks плюс FAISS HNSW dense ANN-search
- Production-default для retrieval-моделей: `Qwen/Qwen3-Embedding-0.6B` и `Qwen/Qwen3-Reranker-0.6B`
- Планируемый generator-default: `Qwen/Qwen3-0.6B` через `Qwen/Qwen3-0.6B-GGUF:Q8_0`
- `python -m pytest backend/tests -q`
- Результат после переключения retrieval на FAISS HNSW backend: `5 passed`
- Текущий рекомендуемый RTX 4090 baseline для перевода: `python -m tooling.translation.translate_esco_to_russian --text-batch-size 64 --record-batch-size 8 --num-beams 1 --max-source-length 256 --max-new-tokens 256`
