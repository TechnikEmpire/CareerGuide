# CareerGuide

Web-based personalized LLM for task oriented career development.

Веб-ориентированный персонализированный LLM для карьерного развития с практической направленностью.

Russian-first for end users. English documentation is maintained for collaboration and review.

Проект ориентирован в первую очередь на русскоязычных пользователей. Английская документация поддерживается для совместной работы и ревью.

The repository now tracks the processed ESCO source layer needed to continue implementation: normalized concept artifacts, normalized relation artifacts, the bilingual translated concept corpus, preprocessing manifests, and the persisted FAISS retrieval cache for the active Qwen3 retrieval configuration. Raw ESCO vendor downloads remain ignored.

Репозиторий теперь отслеживает обработанный ESCO source layer, необходимый для продолжения реализации: нормализованные concept-артефакты, нормализованные relation-артефакты, двуязычный translated concept corpus, preprocessing manifests и persisted FAISS retrieval cache для активной конфигурации Qwen3 retrieval. Raw ESCO vendor downloads по-прежнему игнорируются.

The current backend retrieval path uses SQLite for persisted ESCO chunks and metadata, FAISS HNSW for dense ANN retrieval, and `Qwen/Qwen3-Embedding-0.6B` as the active baseline embedding model. The tracked retrieval-eval outputs now show that `Qwen/Qwen3-Reranker-0.6B` hurts ranking quality while adding substantial runtime cost, so reranking is disabled by default and is not part of the active runtime path.

The current dense-only tuning curve shows an obvious elbow at `top_k=10`, so
the active retrieval default is now locked to `top_k=10`. Because reranking is
off, `candidate_pool` no longer changes the live dense-only runtime path and is
kept only for explicit ablation or future reranker experiments.

Текущий backend retrieval path использует SQLite для хранения persisted ESCO chunks и metadata, FAISS HNSW — для dense ANN-retrieval, а `Qwen/Qwen3-Embedding-0.6B` является активной baseline embedding-моделью. Отслеживаемые retrieval-eval outputs теперь показывают, что `Qwen/Qwen3-Reranker-0.6B` ухудшает ranking quality и при этом добавляет заметную runtime-стоимость, поэтому reranking отключен по умолчанию и не входит в активный runtime-path.

Текущая dense-only tuning-кривая показывает явный elbow на `top_k=10`, поэтому
активный retrieval-default теперь зафиксирован на `top_k=10`. Поскольку
reranking выключен, `candidate_pool` больше не меняет live dense-only
runtime-path и сохраняется только для явных ablation-экспериментов или
возможных будущих экспериментов с reranker.

The active generator target is `Qwen/Qwen3-0.6B` via a local `llama.cpp`-backed GGUF server, using the official GGUF distribution `Qwen/Qwen3-0.6B-GGUF:Q8_0`.

Активный generator-target теперь - `Qwen/Qwen3-0.6B` через локальный GGUF-server на базе `llama.cpp`, с использованием официального GGUF-дистрибутива `Qwen/Qwen3-0.6B-GGUF:Q8_0`.

The real generator client is now wired against an OpenAI-compatible local
generation server at `/v1/chat/completions`. The preferred local implementation
is `llama-cpp-python[server]`, not a hand-built `llama-server` binary. Runtime
validation is still an operator task: install the optional runtime package,
start the local server, then run the canonical answer-export and scoring
commands.

Реальный generator client теперь подключен к локальному OpenAI-compatible
generation-server по адресу `/v1/chat/completions`. Предпочтительная локальная
реализация - `llama-cpp-python[server]`, а не вручную собранный бинарник
`llama-server`. Runtime-валидация все еще остается операторской задачей:
сначала нужно установить optional runtime-пакет, затем запустить локальный
server и выполнить канонические команды экспорта и scoring для answer-output.

The next validation pass should refresh the generated-answer outputs, because
the prompt and runtime defaults are now tighter than the currently persisted
answer-eval baseline. Answer-evidence scoring now depends on explicit
model-selected `cited_chunk_ids`, not on treating the entire retrieved context
as if it had been cited.

Следующий validation-pass должен обновить generated-answer outputs, потому что
prompt и runtime-default теперь жестче, чем в текущем persisted
answer-eval-baseline. Score для answer-evidence теперь зависит от явных
model-selected `cited_chunk_ids`, а не от предположения, что весь retrieved
context был процитирован.

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

The repo now includes a canonical local operator workflow for real local-model
runs.

Репозиторий теперь включает канонический локальный operator-workflow для
реальных запусков с локальными моделями.

The repo now also includes standalone ru/en synthetic-data and BiLSTM training
tooling for sentence-level memory extraction under
`tooling/memory_extraction/`. This tooling remains separate from generation and
retrieval training, but the tracked binary bundle is now wired into the live
backend write path. The runtime now prefers `pySBD` sentence segmentation and
falls back to a lightweight regex splitter if `pysbd` is not yet installed in
the local app environment. The raw synthetic corpus keeps fine-grained memory
labels, but the first supervised extractor baseline remains a binary
`MEMORY` vs `NO_MEMORY` classifier before any later type-classification phase.
Synthetic corpus generation for this tooling is direct local-model GPU work,
not routed through the app server. The live runtime shape is now explicit:
split one user turn into sentence-like segments, classify each segment
independently, upsert only the positive segments into `memory_items`, and let
the existing Hopfield read work over that deduplicated persistent store.

Репозиторий теперь также включает standalone tooling для synthetic-data на
`ru`/`en` и обучения BiLSTM для sentence-level memory extraction в
`tooling/memory_extraction/`. Это tooling по-прежнему отделено от обучения
generation/retrieval, но отслеживаемый binary bundle теперь уже подключен к
live backend write-path. Runtime теперь предпочитает sentence-splitting через
`pySBD` и откатывается к легкому regex-splitter, если `pysbd` еще не установлен
в локальном app-env. Raw synthetic corpus сохраняет fine-grained memory labels,
но первый supervised baseline extractor по-прежнему остается binary-classifier
`MEMORY` vs `NO_MEMORY`, а более поздняя type-classification phase откладывается
после этого baseline. Генерация synthetic corpus для этого tooling выполняется
как direct local-model GPU workflow, а не через app-server. Live runtime-схема
теперь явно зафиксирована: один user turn разбивается на sentence-like
segments, каждый segment независимо классифицируется, только positive segments
upsert-ятся в `memory_items`, а существующий Hopfield-read работает уже поверх
этого дедуплицированного persistent store.

The repository now also contains the first real web UI slice under `frontend/`.
It is a lightweight React + Vite client that talks directly to the existing
FastAPI backend instead of introducing a second AI orchestration layer. The
current UI already covers profile selection, chat, citations, “memory used”,
structured plan generation with study preferences, scheduled-plan preview,
`.ics` export, and a memory inspector backed by `/memory/list`.

Репозиторий теперь также содержит первый реальный slice web UI в `frontend/`.
Это легкий клиент на React + Vite, который напрямую работает с существующим
FastAPI-backend и не вводит второй orchestration-layer для AI. Текущий UI уже
поддерживает выбор профиля, чат, citations, отображение “memory used”,
structured plan generation со study-preferences, preview расписания плана,
`.ics`-экспорт и memory inspector поверх `/memory/list`.

## Authoritative Repository Docs

- `AGENTS.md` - canonical working guide for AI coding agents
- `docs/PROJECT_CHARTER.md` - project purpose, scope, and academic framing
- `docs/ENGINEERING_STANDARDS.md` - code quality, modularity, comments, and documentation rules
- `docs/DECISIONS.md` - active architectural and scope decisions
- `docs/SETUP.md` - local environment setup for WSL, Windows, and macOS
- `docs/BENCHMARKS.md` - canonical retrieval benchmark workflow and interpretation
- `docs/EVALUATION.md` - canonical retrieval and answer-quality evaluation policy
- `docs/LOCAL_WORKFLOW.md` - current local operator workflow and what each step does
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
- `docs/LOCAL_WORKFLOW.md` - текущий локальный operator-workflow и назначение каждого шага
- `docs/ROADMAP.md` - долгосрочные стадии реализации
- `docs/STATUS.md` - текущий снимок проекта и ближайшие шаги
- `docs/ESCO_PREPROCESSING.md` - one-time workflow нормализации и перевода ESCO

## Local Environment

Use the bilingual setup guide here:

- `docs/SETUP.md`

For the current real local-model workflow, use:

- `docs/LOCAL_WORKFLOW.md`

Default Conda environment name:

```text
careerguide
```

Quick test command:

```bash
python -m pytest backend/tests -q
```

Frontend install and build:

```bash
cd frontend
npm install
npm run build
```

Run the frontend dev server:

```bash
cd frontend
npm run dev
```

Default frontend URL:

```text
http://127.0.0.1:5173
```

Default backend API base URL expected by the frontend:

```text
http://127.0.0.1:8000
```

If the backend runs elsewhere, set `VITE_API_BASE_URL` before starting the
frontend.

Targeted tests for the current Hopfield-memory slice:

```bash
python -m pytest backend/tests/test_hopfield_memory.py -q
python -m pytest backend/tests/test_memory_store.py -q
python -m pytest backend/tests/test_app.py -q
python -m pytest backend/tests/test_dev_server_scripts.py -q
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
python -m backend.scripts.export_retrieval_predictions --output-json eval/out/retrieval_predictions_dense.json
```

Canonical dense-only tuning export:

```bash
python -m backend.scripts.run_local_eval_workflow
```

The local evaluation workflow now validates retrieval artifacts up front and
refreshes them automatically if the local SQLite rows or FAISS metadata are
stale.

Canonical local runtime setup:

```bash
python -m backend.scripts.setup_local_models
python -m backend.scripts.run_local_app_stack --reload
```

The single stack command starts the model runtime and the FastAPI app together.
If the local generation server is already running, it reuses it. The backend
startup path now also repairs stale retrieval artifacts automatically before
serving requests.

`Baseline RAG v1 Complete` is now the closed baseline boundary for the current
scope. The active milestone is `Memory Layer v1 Integrated`: user memory now
persists in SQLite across requests, and the live `/chat/answer` flow
automatically extracts simple user-constraint memory candidates before building
retrieval context. What is still missing is the real `RAG-only` versus
`RAG + memory` evaluation loop plus richer editable profile/artifact memory.

The live memory-read path now uses a basic non-trainable Hopfield mechanism
over real embedding-space memory vectors. It supports explicit `top1`
max-energy recall and `topk` sparse superposed recall. This phase is grounded
in Davydov, Jaffe, Singh, and Bullo, "Retrieving k-Nearest Memories with
Modern Hopfield Networks"; the committed repo sources are
`docs/papers/33_Retrieving_k_Nearest_Memori.pdf` and
`docs/papers/hopfield_memory.txt`. Learned projections and differentiable
`ksoftmax` remain future work rather than current claims.

`Baseline RAG v1 Complete` теперь является закрытой baseline-границей для
текущего scope. Активная веха теперь называется `Memory Layer v1 Integrated`:
user memory теперь сохраняется в SQLite между запросами, а live-flow
`/chat/answer` автоматически извлекает простые memory-candidates для
user-constraints до построения retrieval-context. Еще не хватает реального
evaluation-цикла `RAG-only` против `RAG + memory`, а также более богатой
редактируемой profile/artifact memory.

Текущий live-path для memory-read теперь использует базовый нетренируемый
Hopfield-механизм поверх memory-векторов в реальном embedding-space. Он
поддерживает явные режимы `top1` для max-energy recall и `topk` для sparse
superposed recall. Этот этап опирается на работу Davydov, Jaffe, Singh и
Bullo "Retrieving k-Nearest Memories with Modern Hopfield Networks"; в
репозитории для этого уже зафиксированы файлы
`docs/papers/33_Retrieving_k_Nearest_Memori.pdf` и
`docs/papers/hopfield_memory.txt`. Learned projections и differentiable
`ksoftmax` остаются будущей работой, а не текущим утверждением.

Canonical persisted retrieval-eval outputs now live under:

- `eval/out/retrieval_predictions_dense.json`
- `eval/out/retrieval_predictions_rerank.json`
- `eval/out/retrieval_scores_dense.json`
- `eval/out/retrieval_scores_rerank.json`
- `eval/out/dense_retrieval_tuning.json`
- `eval/out/answer_predictions.json`
- `eval/out/answer_scores.json`

The dense files document the active baseline. The reranker files are retained as
negative-ablation evidence for the current tracked qrels.
The answer files are only meaningful when they were produced by the explicit
citation path that exports model-selected `cited_chunk_ids`.

## Локальное окружение

Используйте двуязычное руководство по настройке здесь:

- `docs/SETUP.md`

Для текущего workflow с реальными локальными моделями используйте:

- `docs/LOCAL_WORKFLOW.md`

Имя Conda-окружения по умолчанию:

```text
careerguide
```

Быстрая команда для запуска тестов:

```bash
python -m pytest backend/tests -q
```

Установка frontend и проверка сборки:

```bash
cd frontend
npm install
npm run build
```

Запуск frontend dev-server:

```bash
cd frontend
npm run dev
```

URL frontend по умолчанию:

```text
http://127.0.0.1:5173
```

Backend API base URL по умолчанию, который ожидает frontend:

```text
http://127.0.0.1:8000
```

Если backend работает в другом месте, задайте `VITE_API_BASE_URL` перед
запуском frontend.

Целевые тесты для текущего Hopfield-memory slice:

```bash
python -m pytest backend/tests/test_hopfield_memory.py -q
python -m pytest backend/tests/test_memory_store.py -q
python -m pytest backend/tests/test_app.py -q
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
python -m backend.scripts.export_retrieval_predictions --output-json eval/out/retrieval_predictions_dense.json
```

Канонический экспорт dense-only tuning:

```bash
python -m backend.scripts.run_local_eval_workflow
```

Локальный evaluation-workflow теперь сначала проверяет retrieval-артефакты и
автоматически обновляет их, если локальные SQLite-rows или FAISS-metadata
устарели.

Канонический setup локального runtime:

```bash
python -m backend.scripts.setup_local_models
python -m backend.scripts.run_local_app_stack --reload
```

Единая команда stack запускает runtime модели и FastAPI app вместе. Если
локальный generation-server уже работает, она повторно использует его. Startup
backend теперь также автоматически восстанавливает устаревшие
retrieval-артефакты до начала обслуживания запросов.

Канонические persisted retrieval-eval output теперь находятся в:

- `eval/out/retrieval_predictions_dense.json`
- `eval/out/retrieval_predictions_rerank.json`
- `eval/out/retrieval_scores_dense.json`
- `eval/out/retrieval_scores_rerank.json`
- `eval/out/dense_retrieval_tuning.json`
- `eval/out/answer_predictions.json`
- `eval/out/answer_scores.json`

Dense-файлы документируют активный baseline. Файлы reranker сохраняются как
доказательство отрицательного ablation-result на текущих отслеживаемых qrels.
Answer-файлы имеют смысл только тогда, когда они получены через explicit
citation-path, экспортирующий model-selected `cited_chunk_ids`.

## Planning Docs

- `plan/codex_execution_plan_career_rag_hopfield.md`
- `plan/codex_plan_career_rag_hopfield_webapp.md`

## Примечание

Долговечная документация репозитория ведется на английском и русском языках. Код и идентификаторы в коде остаются на английском языке ради единообразия и сопровождаемости.
