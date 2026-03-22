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
| 1. Corpus acquisition and normalization | in_progress | Ingestion module entry points exist, but real authoritative source ingestion and normalized artifacts are not implemented yet. |
| 2. Embeddings and retrieval index | scaffolded | A transparent retrieval scaffold exists, but the real SQLite corpus index, multilingual embeddings, and rebuild flow are still pending. |
| 3. Reranking and baseline RAG | scaffolded | API shape and stub generation exist, but real multilingual reranking and `llama.cpp` generation are not wired yet. |
| 4. User profile and artifact memory | scaffolded | Memory schemas and in-process storage exist, but editable persistent profile and artifact storage are not finished. |
| 5. Memory extraction and consolidation | scaffolded | Basic extraction and consolidation modules exist, but the actual robust flow is still pending. |
| 6. Hopfield-style memory read | scaffolded | The associative read module exists and is tested at a scaffold level, but it still needs production data flow and debug artifact logging. |
| 7. Joint RAG + memory generation | scaffolded | Prompt assembly already includes retrieval and memory summary structure, but the full comparison modes and evidence-priority behavior are still pending. |
| 8. Safety and refusal behavior | scaffolded | There is a minimal scope guard, but the real risk-policy layer is not complete. |
| 9. Evaluation harness | in_progress | Bilingual scenarios and placeholder runners exist, but full baseline execution and scoring are not implemented yet. |
| 10. Optional browser inference experiment | optional | Explicitly deferred until the backend-first system is stable. |

### Current Trajectory

The most important next implementation path remains:

1. real corpus ingestion
2. real multilingual retrieval index
3. real multilingual reranking
4. real `llama.cpp` generator integration
5. persistent memory and evaluation maturity

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
| 1. Сбор корпуса и нормализация | in_progress | Точки входа для ingestion-модулей существуют, но реальная загрузка авторитетных источников и нормализованные артефакты еще не реализованы. |
| 2. Эмбеддинги и retrieval index | scaffolded | Прозрачный retrieval-scaffold уже есть, но настоящий SQLite-индекс корпуса, multilingual embeddings и воспроизводимая сборка еще не готовы. |
| 3. Reranking и baseline RAG | scaffolded | Форма API и stub-generation уже есть, но настоящий multilingual reranking и генерация через `llama.cpp` еще не подключены. |
| 4. User profile и artifact memory | scaffolded | Схемы памяти и in-process storage уже есть, но редактируемый persistent profile и artifact storage еще не завершены. |
| 5. Извлечение памяти и консолидация | scaffolded | Базовые модули extraction и consolidation уже есть, но полноценный надежный flow еще впереди. |
| 6. Hopfield-style memory read | scaffolded | Модуль associative read уже существует и протестирован на уровне scaffold, но ему еще нужен production data flow и логирование debug-артефактов. |
| 7. Совместная генерация RAG + memory | scaffolded | Prompt assembly уже включает структуру retrieval и memory summary, но полноценные режимы сравнения и приоритет evidence над unsupported claims еще впереди. |
| 8. Safety и refusal behavior | scaffolded | Есть минимальная scope-защита, но полноценный risk-policy layer еще не завершен. |
| 9. Evaluation harness | in_progress | Уже есть двуязычные сценарии и placeholder runners, но полный запуск baseline-режимов и scoring пока не реализован. |
| 10. Optional browser inference experiment | optional | Явно отложено до тех пор, пока backend-first система не станет стабильной. |

### Текущая траектория

Наиболее важная следующая последовательность реализации остается такой:

1. реальная загрузка корпуса
2. реальный multilingual retrieval index
3. реальный multilingual reranking
4. реальная интеграция генератора через `llama.cpp`
5. развитие persistent memory и evaluation
