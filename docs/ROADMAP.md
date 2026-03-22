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
| 1. Corpus acquisition and normalization | completed | ESCO English source ingestion, normalization, deduplication, and tracked bilingual preprocessing artifacts are now in place for the current first-source scope. |
| 2. Embeddings and retrieval index | in_progress | The main retrieval path now uses SQLite-persisted ESCO chunks, FAISS HNSW dense ANN search, and Qwen3 retrieval-model defaults, but the explicit rebuild flow and runtime benchmarking are still pending. |
| 3. Reranking and baseline RAG | in_progress | The codebase now targets `Qwen/Qwen3-Reranker-0.6B` for reranking and `Qwen/Qwen3-0.6B` for generation, but the full runtime path still needs benchmark validation and real `llama.cpp` generation. |
| 4. User profile and artifact memory | scaffolded | Memory schemas and in-process storage exist, but editable persistent profile and artifact storage are not finished. |
| 5. Memory extraction and consolidation | scaffolded | Basic extraction and consolidation modules exist, but the actual robust flow is still pending. |
| 6. Hopfield-style memory read | scaffolded | The associative read module exists and is tested at a scaffold level, but it still needs production data flow and debug artifact logging. |
| 7. Joint RAG + memory generation | scaffolded | Prompt assembly already includes retrieval and memory summary structure, but the full comparison modes and evidence-priority behavior are still pending. |
| 8. Safety and refusal behavior | scaffolded | There is a minimal scope guard, but the real risk-policy layer is not complete. |
| 9. Evaluation harness | in_progress | Bilingual scenarios and placeholder runners exist, but full baseline execution and scoring are not implemented yet. |
| 10. Optional browser inference experiment | optional | Explicitly deferred until the backend-first system is stable. |

### Current Trajectory

The most important next implementation path remains:

1. add explicit FAISS/SQLite corpus build and refresh commands
2. benchmark and tune the Qwen3 embedding/reranking path
3. real `llama.cpp` generator integration with `Qwen/Qwen3-0.6B`
4. persistent memory and evaluation maturity

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
| 1. Сбор корпуса и нормализация | completed | Для текущего scope первого источника уже реализованы загрузка ESCO English source, normalization, deduplication и отслеживаемые двуязычные preprocessing-артефакты. |
| 2. Эмбеддинги и retrieval index | in_progress | Основной retrieval path теперь использует SQLite-persisted ESCO chunks, FAISS HNSW dense ANN index и Qwen3-default для retrieval-моделей, но явный rebuild flow и runtime-benchmarking еще не завершены. |
| 3. Reranking и baseline RAG | in_progress | Кодовая база теперь ориентирована на `Qwen/Qwen3-Reranker-0.6B` для reranking и `Qwen/Qwen3-0.6B` для генерации, но полный runtime-path все еще требует benchmark-валидации и реальной интеграции через `llama.cpp`. |
| 4. User profile и artifact memory | scaffolded | Схемы памяти и in-process storage уже есть, но редактируемый persistent profile и artifact storage еще не завершены. |
| 5. Извлечение памяти и консолидация | scaffolded | Базовые модули extraction и consolidation уже есть, но полноценный надежный flow еще впереди. |
| 6. Hopfield-style memory read | scaffolded | Модуль associative read уже существует и протестирован на уровне scaffold, но ему еще нужен production data flow и логирование debug-артефактов. |
| 7. Совместная генерация RAG + memory | scaffolded | Prompt assembly уже включает структуру retrieval и memory summary, но полноценные режимы сравнения и приоритет evidence над unsupported claims еще впереди. |
| 8. Safety и refusal behavior | scaffolded | Есть минимальная scope-защита, но полноценный risk-policy layer еще не завершен. |
| 9. Evaluation harness | in_progress | Уже есть двуязычные сценарии и placeholder runners, но полный запуск baseline-режимов и scoring пока не реализован. |
| 10. Optional browser inference experiment | optional | Явно отложено до тех пор, пока backend-first система не станет стабильной. |

### Текущая траектория

Наиболее важная следующая последовательность реализации остается такой:

1. добавить явные команды corpus build и refresh для FAISS/SQLite
2. замерить и настроить путь Qwen3 embeddings + reranking
3. реальная интеграция генератора `Qwen/Qwen3-0.6B` через `llama.cpp`
4. развитие persistent memory и evaluation
