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
| 4. LLM grounding and structured generation | in_progress | Retrieval-backed prompt assembly exists, but the real `llama.cpp` generator client for `Qwen/Qwen3-0.6B` is not wired yet. |
| 5. User profile and artifact memory | scaffolded | Memory schemas and in-process storage exist, but editable persistent profile and artifact storage are not finished. |
| 6. Memory extraction and consolidation | scaffolded | Basic extraction and consolidation modules exist, but the robust flow is still pending. |
| 7. Hopfield-style memory read | scaffolded | The associative read module exists and is tested at a scaffold level, but it still needs production data flow and debug artifact logging. |
| 8. Joint RAG + memory generation | scaffolded | Prompt assembly already includes retrieval and memory summary structure, but the full comparison modes and evidence-priority behavior are still pending. |
| 9. Safety and refusal behavior | scaffolded | There is a minimal scope guard, but the real risk-policy layer is not complete. |
| 10. Evaluation harness | in_progress | Canonical retrieval qrels, answer-evaluation cases, score utilities, and persisted retrieval outputs now exist. The next work is answer-level scoring over real generated outputs and dense-only top-k sweeps. |
| 11. Optional browser inference experiment | optional | Explicitly deferred until the backend-first system is stable. |

### Current Trajectory

The most important next implementation path is now:

1. real `llama.cpp` generator integration with `Qwen/Qwen3-0.6B`
2. dense-only top-k and candidate-pool ablations against the tracked qrels
3. answer-level evaluation over generated outputs
4. persistent memory and evaluation maturity

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
| 4. LLM grounding и structured generation | in_progress | Retrieval-backed prompt assembly уже существует, но реальный `llama.cpp` generator client для `Qwen/Qwen3-0.6B` еще не подключен. |
| 5. User profile и artifact memory | scaffolded | Схемы памяти и in-process storage уже есть, но редактируемый persistent profile и artifact storage еще не завершены. |
| 6. Извлечение памяти и консолидация | scaffolded | Базовые модули extraction и consolidation уже есть, но полноценный надежный flow еще впереди. |
| 7. Hopfield-style memory read | scaffolded | Модуль associative read уже существует и протестирован на уровне scaffold, но ему еще нужен production data flow и логирование debug-артефактов. |
| 8. Совместная генерация RAG + memory | scaffolded | Prompt assembly уже включает структуру retrieval и memory summary, но полноценные режимы сравнения и приоритет evidence над unsupported claims еще впереди. |
| 9. Safety и refusal behavior | scaffolded | Есть минимальная scope-защита, но полноценный risk-policy layer еще не завершен. |
| 10. Evaluation harness | in_progress | Канонические retrieval qrels, answer-evaluation cases, scoring-утилиты и persisted retrieval outputs уже существуют. Следующая работа - answer-level scoring на реально сгенерированных ответах и dense-only sweeps по top-k. |
| 11. Optional browser inference experiment | optional | Явно отложено до тех пор, пока backend-first система не станет стабильной. |

### Текущая траектория

Наиболее важная следующая последовательность реализации теперь такая:

1. реальная интеграция генератора `Qwen/Qwen3-0.6B` через `llama.cpp`
2. dense-only ablation по top-k и candidate-pool на отслеживаемых qrels
3. answer-level evaluation на сгенерированных ответах
4. развитие persistent memory и evaluation

Тюнинг reranker не находится на критическом пути. Текущие отслеживаемые qrels
показывают, что reranking ухудшает ranking quality и добавляет стоимость, так
что он не входит в активный runtime-baseline.
