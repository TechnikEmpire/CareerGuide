# Project Roadmap

## English

### Purpose

This file is the long-horizon implementation map for the project.

Use it to answer:

- what stages exist
- what each stage is supposed to deliver
- what the current status of each stage is

For the short-term snapshot, use `docs/STATUS.md`.

### Status Legend

- `completed` = done and accepted for the current scope
- `in_progress` = active work is happening now
- `scaffolded` = basic structure exists, but the real implementation is not done
- `not_started` = planned, but not yet implemented
- `optional` = only do this if core goals are already stable

### Roadmap

| Stage | Status | Summary |
| --- | --- | --- |
| 0. Repo foundation and governance | completed | Bilingual repo guidance, setup docs, engineering standards, decisions log, and initial scaffold are in place. |
| 1. Corpus acquisition and normalization | completed | ESCO ingestion, normalization, deduplication, bilingual translation, and tracked preprocessing artifacts are now in place for the current first-source scope. |
| 2. Embeddings and retrieval index | completed | The active retrieval path now uses SQLite-persisted ESCO chunks, FAISS HNSW dense ANN search, Qwen3 embedding defaults, an explicit build command, and tracked FAISS cache artifacts. |
| 3. Baseline RAG retrieval | completed | The repo now has canonical CPU-only HNSW benchmarking, tracked qrels, scored dense-versus-reranker outputs, and a measured decision to keep dense-only retrieval as the active baseline. |
| 4. LLM grounding and structured generation | completed | Retrieval-backed prompt assembly, the real OpenAI-compatible local generator client, explicit citation export, and baseline answer validation are now in place. The dense-only default is locked at `top_k=10`, and `Baseline RAG v1 Complete` is now closed for the current scope. |
| 5. User profile and artifact memory | scaffolded | Memory schemas and in-process storage exist, but editable persistent profile and artifact storage are not finished. |
| 6. Memory extraction and consolidation | scaffolded | Basic extraction and consolidation modules exist, but the robust flow is still pending. |
| 7. Hopfield-style memory read | scaffolded | The associative read module exists and is tested at a scaffold level, but it still needs production data flow and debug artifact logging. |
| 8. Joint RAG + memory generation | scaffolded | Prompt assembly already includes retrieval and memory summary structure, but the full comparison modes and evidence-priority behavior are still pending. |
| 9. Safety and refusal behavior | scaffolded | There is a minimal scope guard, but the real risk-policy layer is not complete. |
| 10. Evaluation harness | in_progress | Canonical retrieval qrels, answer-evaluation cases, score utilities, dense-only tuning export, and answer-export tooling now exist. The dense-only elbow is locked at `top_k=10`, explicit citation export is now working, and the next work is extending the harness to `RAG-only` versus `RAG + memory` comparison. |
| 11. Optional browser inference experiment | optional | Explicitly deferred until the backend-first system is stable. |

### Current Trajectory

The most important next implementation path is now:

1. validate the wired local generation server against the active API and answer-export flow
2. refresh and review generated answers under the locked dense-only default `top_k=10`
3. improve prompt/citation behavior from the scored answer outputs, now that answer-evidence scoring is based on explicit cited chunk IDs
4. persistent memory and evaluation maturity

### Next Clean Boundary

The next clean project boundary is:

- `Memory Layer v1 Integrated`

That boundary closes when the project has:

1. persistent user-profile and artifact memory storage
2. live extraction and consolidation in the production flow
3. Hopfield-style associative read connected to generation
4. measurable `RAG-only` versus `RAG + memory` comparison
5. updated persisted eval outputs and docs reflecting the memory-enabled system

Reranker tuning is not on the critical path. The current tracked qrels show
that reranking hurts ranking quality and adds cost, so it is not part of the
active runtime baseline.

## Русский

### Назначение

Этот файл является долгосрочной картой реализации проекта.

Он нужен, чтобы отвечать на вопросы:

- какие стадии вообще существуют
- что каждая стадия должна дать
- каков текущий статус каждой стадии

Для краткосрочного текущего снимка используйте `docs/STATUS.md`.

### Легенда статусов

- `completed` = выполнено и принято в рамках текущего scope
- `in_progress` = по этой стадии сейчас идет активная работа
- `scaffolded` = базовая структура уже есть, но реальная реализация еще не завершена
- `not_started` = запланировано, но еще не начато
- `optional` = выполнять только после стабилизации основных целей

### Дорожная карта

| Stage | Status | Summary |
| --- | --- | --- |
| 0. Основа репозитория и governance | completed | Созданы двуязычные правила репозитория, setup-документация, engineering standards, decisions log и начальный scaffold. |
| 1. Сбор корпуса и нормализация | completed | Для текущего scope первого источника уже реализованы ingestion ESCO, normalization, deduplication, bilingual translation и отслеживаемые preprocessing-артефакты. |
| 2. Эмбеддинги и retrieval index | completed | Активный retrieval-path теперь использует SQLite-persisted ESCO chunks, FAISS HNSW dense ANN search, Qwen3-default для embeddings, явную команду сборки и отслеживаемые FAISS cache-артефакты. |
| 3. Baseline RAG retrieval | completed | В репозитории теперь есть канонический CPU-only HNSW benchmark, отслеживаемые qrels, scored dense-versus-reranker outputs и уже измеренное решение оставить dense-only retrieval активным baseline. |
| 4. LLM grounding и structured generation | completed | Retrieval-backed prompt assembly, реальный локальный OpenAI-compatible generator client, explicit citation export и baseline validation ответов уже реализованы. Dense-only default зафиксирован на `top_k=10`, а `Baseline RAG v1 Complete` теперь закрыт в рамках текущего scope. |
| 5. User profile и artifact memory | scaffolded | Схемы памяти и in-process storage уже есть, но редактируемый persistent profile и artifact storage еще не завершены. |
| 6. Извлечение памяти и консолидация | scaffolded | Базовые модули extraction и consolidation уже есть, но полноценный надежный flow еще впереди. |
| 7. Hopfield-style memory read | scaffolded | Модуль associative read уже существует и протестирован на уровне scaffold, но ему еще нужен production data flow и логирование debug-артефактов. |
| 8. Совместная генерация RAG + memory | scaffolded | Prompt assembly уже включает структуру retrieval и memory summary, но полноценные режимы сравнения и приоритет evidence над unsupported claims еще впереди. |
| 9. Safety и refusal behavior | scaffolded | Есть минимальная scope-защита, но полноценный risk-policy layer еще не завершен. |
| 10. Evaluation harness | in_progress | Канонические retrieval qrels, answer-evaluation cases, scoring-утилиты, dense-only tuning export и answer-export tooling уже существуют. Dense-only elbow зафиксирован на `top_k=10`, explicit citation export теперь работает, и следующая работа — расширить harness до сравнения `RAG-only` и `RAG + memory`. |
| 11. Optional browser inference experiment | optional | Явно отложено до тех пор, пока backend-first система не станет стабильной. |

### Текущая траектория

Наиболее важная следующая последовательность реализации теперь такая:

1. провалидировать уже подключенный локальный generation-server через активный API и answer-export flow
2. обновить и разобрать generated-answer outputs уже под зафиксированным dense-only default `top_k=10`
3. улучшить prompt/citation behavior на основе scored answer-output, где answer-evidence теперь считается по явным cited chunk IDs
4. развитие persistent memory и evaluation

### Следующая чистая граница

Следующая чистая граница проекта называется:

- `Memory Layer v1 Integrated`

Эта граница закрывается тогда, когда проект имеет:

1. persistent storage для user profile и artifact memory
2. живые extraction и consolidation в production flow
3. подключенный к generation Hopfield-style associative read
4. измеряемое сравнение `RAG-only` и `RAG + memory`
5. обновленные persisted eval-output и документацию, отражающие memory-enabled system

Тюнинг reranker не находится на критическом пути. Текущие отслеживаемые qrels
показывают, что reranking ухудшает ranking quality и добавляет стоимость, так
что он не входит в активный runtime-baseline.
