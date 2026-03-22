# CareerGuide

Web-based personalized LLM for task oriented career development.

Веб-ориентированный персонализированный LLM для карьерного развития с практической направленностью.

Russian-first for end users. English documentation is maintained for collaboration and review.

Проект ориентирован в первую очередь на русскоязычных пользователей. Английская документация поддерживается для совместной работы и ревью.

The repository now tracks the processed ESCO source layer needed to continue implementation: normalized concept artifacts, normalized relation artifacts, the bilingual translated concept corpus, preprocessing manifests, and the persisted FAISS retrieval cache for the active Qwen3 retrieval configuration. Raw ESCO vendor downloads remain ignored.

Репозиторий теперь отслеживает обработанный ESCO source layer, необходимый для продолжения реализации: нормализованные concept-артефакты, нормализованные relation-артефакты, двуязычный translated concept corpus, preprocessing manifests и persisted FAISS retrieval cache для активной конфигурации Qwen3 retrieval. Raw ESCO vendor downloads по-прежнему игнорируются.

The current backend retrieval path uses SQLite for persisted ESCO chunks and metadata, FAISS HNSW for dense ANN retrieval, and `Qwen/Qwen3-Embedding-0.6B` as the active baseline embedding model. The tracked retrieval-eval outputs now show that `Qwen/Qwen3-Reranker-0.6B` hurts ranking quality while adding substantial runtime cost, so reranking is disabled by default and is not part of the active runtime path.

Текущий backend retrieval path использует SQLite для хранения persisted ESCO chunks и metadata, FAISS HNSW — для dense ANN-retrieval, а `Qwen/Qwen3-Embedding-0.6B` является активной baseline embedding-моделью. Отслеживаемые retrieval-eval outputs теперь показывают, что `Qwen/Qwen3-Reranker-0.6B` ухудшает ranking quality и при этом добавляет заметную runtime-стоимость, поэтому reranking отключен по умолчанию и не входит в активный runtime-path.

The planned generator default is now `Qwen/Qwen3-0.6B` via `llama.cpp`, using the official GGUF distribution `Qwen/Qwen3-0.6B-GGUF:Q8_0`.

Планируемый generator-default теперь - `Qwen/Qwen3-0.6B` через `llama.cpp`, с использованием официального GGUF-дистрибутива `Qwen/Qwen3-0.6B-GGUF:Q8_0`.

Before running the real retrieval-backed backend, build the persisted retrieval store and FAISS index explicitly:

```bash
python -m backend.scripts.build_retrieval_index
```

Перед запуском реального retrieval-backed backend необходимо явно собрать persisted retrieval store и FAISS-index:

```bash
python -m backend.scripts.build_retrieval_index
```

If the tracked FAISS cache is already current but the local SQLite retrieval
rows are missing or stale, this command restores the SQLite rows without a full
corpus re-embedding pass.

Если отслеживаемый FAISS-cache уже актуален, а локальные SQLite retrieval-rows
отсутствуют или устарели, эта команда восстановит SQLite-rows без полного
повторного прохода эмбеддинга по корпусу.

## Authoritative Repository Docs

- `AGENTS.md` - canonical working guide for AI coding agents
- `docs/PROJECT_CHARTER.md` - project purpose, scope, and academic framing
- `docs/ENGINEERING_STANDARDS.md` - code quality, modularity, comments, and documentation rules
- `docs/DECISIONS.md` - active architectural and scope decisions
- `docs/SETUP.md` - local environment setup for WSL, Windows, and macOS
- `docs/BENCHMARKS.md` - canonical retrieval benchmark workflow and interpretation
- `docs/EVALUATION.md` - canonical retrieval and answer-quality evaluation policy
- `docs/ROADMAP.md` - long-horizon implementation stages
- `docs/STATUS.md` - current project snapshot and next steps
- `docs/ESCO_PREPROCESSING.md` - one-time ESCO normalization and translation workflow

## Канонические документы репозитория

- `AGENTS.md` - основное рабочее руководство для ИИ-агентов
- `docs/PROJECT_CHARTER.md` - назначение проекта, границы и академическое позиционирование
- `docs/ENGINEERING_STANDARDS.md` - правила качества кода, модульности, комментариев и документации
- `docs/DECISIONS.md` - активные архитектурные и scope-решения
- `docs/SETUP.md` - настройка локального окружения для WSL, Windows и macOS
- `docs/BENCHMARKS.md` - канонический workflow benchmark для retrieval и правила интерпретации
- `docs/EVALUATION.md` - каноническая политика оценки retrieval и качества ответов
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

Canonical retrieval benchmark:

```bash
python -m backend.scripts.benchmark_retrieval
```

Dense retrieval benchmark on CPU:

```bash
python -m backend.scripts.benchmark_retrieval --mode dense
```

Optional heavy diagnostic benchmark:

```bash
python -m backend.scripts.benchmark_retrieval --mode full --hf-home /tmp/careerguide_hf_cache
```

The benchmark script does not rebuild retrieval artifacts. Build or refresh the
index first with `python -m backend.scripts.build_retrieval_index` if the
benchmark reports stale artifacts.

Canonical evaluation fixtures now live in:

- `eval/retrieval_benchmark_queries.json`
- `eval/retrieval_qrels.json`
- `eval/answer_eval_cases.json`

Canonical retrieval-prediction export:

```bash
python -m backend.scripts.export_retrieval_predictions --output-json eval/out/retrieval_predictions.json
```

Canonical persisted retrieval-eval outputs now live under:

- `eval/out/retrieval_predictions_dense.json`
- `eval/out/retrieval_predictions_rerank.json`
- `eval/out/retrieval_scores_dense.json`
- `eval/out/retrieval_scores_rerank.json`

The dense files document the active baseline. The reranker files are retained as
negative-ablation evidence for the current tracked qrels.

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

Канонический benchmark retrieval:

```bash
python -m backend.scripts.benchmark_retrieval
```

Benchmark dense retrieval на CPU:

```bash
python -m backend.scripts.benchmark_retrieval --mode dense
```

Опциональный тяжелый diagnostic-benchmark:

```bash
python -m backend.scripts.benchmark_retrieval --mode full --hf-home /tmp/careerguide_hf_cache
```

Benchmark-скрипт не пересобирает retrieval-артефакты. Если benchmark сообщает,
что артефакты устарели, сначала выполните `python -m backend.scripts.build_retrieval_index`.

Канонические evaluation-артефакты теперь находятся в:

- `eval/retrieval_benchmark_queries.json`
- `eval/retrieval_qrels.json`
- `eval/answer_eval_cases.json`

Канонический экспорт retrieval-predictions:

```bash
python -m backend.scripts.export_retrieval_predictions --output-json eval/out/retrieval_predictions.json
```

Канонические persisted retrieval-eval output теперь находятся в:

- `eval/out/retrieval_predictions_dense.json`
- `eval/out/retrieval_predictions_rerank.json`
- `eval/out/retrieval_scores_dense.json`
- `eval/out/retrieval_scores_rerank.json`

Dense-файлы документируют активный baseline. Файлы reranker сохраняются как
доказательство отрицательного ablation-result на текущих отслеживаемых qrels.

## Planning Docs

- `plan/codex_execution_plan_career_rag_hopfield.md`
- `plan/codex_plan_career_rag_hopfield_webapp.md`

## Примечание

Долговечная документация репозитория ведется на английском и русском языках. Код и идентификаторы в коде остаются на английском языке ради единообразия и сопровождаемости.
