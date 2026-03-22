# CareerGuide

Web-based personalized LLM for task oriented career development.

Веб-ориентированный персонализированный LLM для карьерного развития с практической направленностью.

Russian-first for end users. English documentation is maintained for collaboration and review.

Проект ориентирован в первую очередь на русскоязычных пользователей. Английская документация поддерживается для совместной работы и ревью.

The repository now tracks the processed ESCO source layer needed to continue implementation: normalized concept artifacts, normalized relation artifacts, the bilingual translated concept corpus, and preprocessing manifests. Raw ESCO vendor downloads remain ignored.

Репозиторий теперь отслеживает обработанный ESCO source layer, необходимый для продолжения реализации: нормализованные concept-артефакты, нормализованные relation-артефакты, двуязычный translated concept corpus и preprocessing manifests. Raw ESCO vendor downloads по-прежнему игнорируются.

The current backend retrieval path uses SQLite for persisted ESCO chunks and metadata, FAISS HNSW for dense ANN retrieval, and `Qwen/Qwen3-Embedding-0.6B` plus `Qwen/Qwen3-Reranker-0.6B` as the production retrieval-model defaults.

Текущий backend retrieval path использует SQLite для хранения persisted ESCO chunks и metadata, FAISS HNSW — для dense ANN-retrieval, а `Qwen/Qwen3-Embedding-0.6B` и `Qwen/Qwen3-Reranker-0.6B` являются production-default для retrieval-моделей.

The planned generator default is now `Qwen/Qwen3-0.6B` via `llama.cpp`, using the official GGUF distribution `Qwen/Qwen3-0.6B-GGUF:Q8_0`.

Планируемый generator-default теперь - `Qwen/Qwen3-0.6B` через `llama.cpp`, с использованием официального GGUF-дистрибутива `Qwen/Qwen3-0.6B-GGUF:Q8_0`.

## Authoritative Repository Docs

- `AGENTS.md` - canonical working guide for AI coding agents
- `docs/PROJECT_CHARTER.md` - project purpose, scope, and academic framing
- `docs/ENGINEERING_STANDARDS.md` - code quality, modularity, comments, and documentation rules
- `docs/DECISIONS.md` - active architectural and scope decisions
- `docs/SETUP.md` - local environment setup for WSL, Windows, and macOS
- `docs/ROADMAP.md` - long-horizon implementation stages
- `docs/STATUS.md` - current project snapshot and next steps
- `docs/ESCO_PREPROCESSING.md` - one-time ESCO normalization and translation workflow

## Канонические документы репозитория

- `AGENTS.md` - основное рабочее руководство для ИИ-агентов
- `docs/PROJECT_CHARTER.md` - назначение проекта, границы и академическое позиционирование
- `docs/ENGINEERING_STANDARDS.md` - правила качества кода, модульности, комментариев и документации
- `docs/DECISIONS.md` - активные архитектурные и scope-решения
- `docs/SETUP.md` - настройка локального окружения для WSL, Windows и macOS
- `docs/ROADMAP.md` - долгосрочные стадии реализации
- `docs/STATUS.md` - текущий снимок проекта и ближайшие шаги
- `docs/ESCO_PREPROCESSING.md` - one-time workflow нормализации и перевода ESCO

## Local Environment

Use the bilingual setup guide here:

- `docs/SETUP.md`

Default Conda environment name:

```text
careerguide
```

Quick test command:

```bash
python -m pytest backend/tests -q
```

## Локальное окружение

Используйте двуязычное руководство по настройке здесь:

- `docs/SETUP.md`

Имя Conda-окружения по умолчанию:

```text
careerguide
```

Быстрая команда для запуска тестов:

```bash
python -m pytest backend/tests -q
```

## Planning Docs

- `plan/codex_execution_plan_career_rag_hopfield.md`
- `plan/codex_plan_career_rag_hopfield_webapp.md`

## Примечание

Долговечная документация репозитория ведется на английском и русском языках. Код и идентификаторы в коде остаются на английском языке ради единообразия и сопровождаемости.
