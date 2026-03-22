# Local Workflow

Last updated: 2026-03-22

Последнее обновление: 2026-03-22

## English

### What This Workflow Is For

This document explains the current local development workflow in plain terms.

At this stage of the project, there are three different kinds of work:

1. one-time corpus preprocessing
2. one-time or infrequent retrieval-index building
3. repeatable local evaluation and answer-generation validation

These are different steps. They are not the same thing.

### What Has Already Been Done

The following heavyweight steps are already completed and tracked in Git:

- ESCO normalization
- English-to-Russian ESCO translation
- FAISS HNSW retrieval-index build
- dense-versus-reranker retrieval evaluation

That means the project is no longer in corpus-preparation mode.

### What The Project Is Doing Now

The active baseline is now:

1. use the tracked ESCO artifacts
2. use the tracked FAISS HNSW retrieval index
3. embed only the incoming query
4. retrieve dense ANN chunks
5. build a grounded prompt
6. ask the local Qwen3 GGUF generator for an answer
7. score the generated answer against tracked answer-eval cases

The active dense-only runtime default is now `top_k=10`, based on the current
tracked tuning curve.

### How Memory Works In The Current App

The local app is no longer using fake in-process-only memory.

At the current stage:

- user memory is persisted in the local SQLite `memory_items` table
- `/chat/answer` now extracts simple memory candidates from the user question
- the persisted memory set is read back immediately and summarized for prompt assembly
- duplicate memory text is collapsed by normalized text per user

This is still a narrow first slice, not the final memory system. The current
heuristic mainly captures explicit preference or constraint phrasing such as
`prefer`, `want`, `need`, `cannot`, or `can't`.

### Как память работает в текущем приложении

Локальное приложение больше не использует фальшивую память только внутри
процесса.

На текущем этапе:

- user memory сохраняется в локальной SQLite-таблице `memory_items`
- `/chat/answer` теперь извлекает простые memory-candidates из вопроса пользователя
- persisted memory сразу читается обратно и суммируется для prompt assembly
- дублирующийся memory-text схлопывается по normalized-text отдельно для каждого пользователя

Это все еще узкий первый slice, а не финальная memory-system. Текущая
эвристика в основном ловит явные формулировки preference или constraint, такие
как `prefer`, `want`, `need`, `cannot` и `can't`.

### Why Local Models Are Still Needed

Even though the retrieval index is already built, answer generation still needs:

- a local generator runtime for `Qwen/Qwen3-0.6B-GGUF:Q8_0`
- a local embedding model for query embedding (`Qwen/Qwen3-Embedding-0.6B`)

The retrieval index stores document vectors, but the system still needs to
embed each incoming query before it can search the index.

The repo-local setup helper writes `.env.local`, and the backend loads that file
automatically. That is how the local query-embedding model path is activated
without manual shell exports.

### Canonical Local Commands

One-time local model setup:

```bash
python -m backend.scripts.setup_local_models
```

Start the full local app stack with one command:

```bash
python -m backend.scripts.run_local_app_stack --reload
```

When `--reload` is enabled, the backend now watches the `backend/` source tree
instead of mutable runtime artifacts like the local SQLite database, model
cache, or eval outputs. That avoids pointless backend restarts after normal app
requests mutate local state.

Когда включен `--reload`, backend теперь следит за деревом исходников
`backend/`, а не за изменяемыми runtime-артефактами вроде локальной SQLite-базы,
model-cache или eval-output. Это предотвращает бессмысленные перезапуски
backend после обычных app-запросов, которые меняют локальное состояние.

If you want to control the two processes manually, the advanced commands are:

```bash
python -m backend.scripts.run_local_generation_server
python -m backend.scripts.run_backend_dev_server --reload
```

Run the canonical local evaluation workflow:

```bash
python -m backend.scripts.run_local_eval_workflow
```

If the local generation server is already running, the evaluation wrapper will
reuse it instead of starting a duplicate process.
If the persisted retrieval artifacts are stale, the wrapper refreshes them
before it starts generation.

### What The Evaluation Workflow Produces

The local evaluation workflow writes three canonical outputs:

- `eval/out/dense_retrieval_tuning.json`
- `eval/out/answer_predictions.json`
- `eval/out/answer_scores.json`

These answer three different questions:

- `dense_retrieval_tuning.json`
  - Which dense-only top-k choice currently scores best on the tracked qrels?
- `answer_predictions.json`
  - What answers and explicit cited chunk IDs did the current retrieval-plus-generation stack produce?
- `answer_scores.json`
  - How well do those generated answers overlap with the expected evidence chunks?

Answer-evidence scoring now depends on model-selected `cited_chunk_ids` rather
than on the full retrieved context list. Any older answer outputs produced
before that citation fix are obsolete and should be regenerated.
The next refresh should validate the new `top_k=10` default, the tighter
generation prompt/runtime settings, and the explicit citation path together.

### What We Are Not Doing

The current workflow is not:

- rebuilding the ESCO translation layer
- rebuilding the FAISS index on every run; it only refreshes retrieval artifacts when they are stale
- using the reranker in the active path
- shipping the final memory-comparison experiment yet

The reranker was already tested and kept only as a negative ablation record.

## Русский

### Для чего нужен этот workflow

Этот документ простыми словами объясняет текущий локальный workflow разработки.

На текущей стадии проекта есть три разных типа работы:

1. one-time preprocessing корпуса
2. one-time или редкая сборка retrieval-index
3. повторяемая локальная evaluation и runtime-валидация генерации ответов

Это разные этапы. Это не одно и то же.

### Что уже сделано

Следующие тяжелые шаги уже завершены и зафиксированы в Git:

- нормализация ESCO
- перевод ESCO с английского на русский
- сборка retrieval-index на базе FAISS HNSW
- evaluation dense-versus-reranker для retrieval

Это означает, что проект уже не находится в режиме подготовки корпуса.

### Что проект делает сейчас

Активный baseline теперь такой:

1. использовать отслеживаемые ESCO-артефакты
2. использовать отслеживаемый retrieval-index на базе FAISS HNSW
3. эмбеддить только входящий query
4. извлекать dense ANN chunks
5. собирать grounded prompt
6. запрашивать ответ у локального Qwen3 GGUF generator
7. score-ить сгенерированный ответ по отслеживаемым answer-eval cases

Активный dense-only runtime-default теперь — `top_k=10`, исходя из текущей
отслеживаемой tuning-кривой.

### Почему локальные модели все еще нужны

Даже если retrieval-index уже собран, генерация ответов все равно требует:

- локальный runtime генератора для `Qwen/Qwen3-0.6B-GGUF:Q8_0`
- локальную embedding-модель для query-эмбеддинга (`Qwen/Qwen3-Embedding-0.6B`)

Retrieval-index хранит document-векторы, но система все равно должна эмбеддить
каждый входящий query до того, как сможет искать по индексу.

Repo-local setup-helper записывает `.env.local`, и backend автоматически
загружает этот файл. Именно так локальный путь к query-embedding-модели
активируется без ручного shell-export.

### Канонические локальные команды

One-time setup локальных моделей:

```bash
python -m backend.scripts.setup_local_models
```

Запуск полного локального app-stack одной командой:

```bash
python -m backend.scripts.run_local_app_stack --reload
```

Если вы хотите вручную управлять двумя процессами, используйте advanced-команды:

```bash
python -m backend.scripts.run_local_generation_server
python -m backend.scripts.run_backend_dev_server --reload
```

Запуск канонического локального evaluation-workflow:

```bash
python -m backend.scripts.run_local_eval_workflow
```

Если локальный generation-server уже работает, evaluation-wrapper повторно
использует его вместо запуска дублирующего процесса.
Если persisted retrieval-артефакты устарели, wrapper обновит их до старта
generation.

### Что производит evaluation-workflow

Локальный evaluation-workflow записывает три канонических output-файла:

- `eval/out/dense_retrieval_tuning.json`
- `eval/out/answer_predictions.json`
- `eval/out/answer_scores.json`

Они отвечают на три разных вопроса:

- `dense_retrieval_tuning.json`
  - Какой выбор dense-only top-k сейчас лучше всего score-ится на отслеживаемых qrels?
- `answer_predictions.json`
  - Какие ответы и какие явные citation-ID chunk-ов выдал текущий retrieval-plus-generation stack?
- `answer_scores.json`
  - Насколько эти сгенерированные ответы пересекаются с ожидаемыми evidence chunks?

Score для answer-evidence теперь зависит от model-selected `cited_chunk_ids`, а
не от полного списка retrieved-context. Любые старые answer-output, созданные
до этого исправления citation-path, считаются устаревшими и должны быть
перегенерированы.
Следующее обновление должно уже провалидировать новый default `top_k=10`,
более жесткие generation prompt/runtime-настройки и сам explicit citation-path.

### Чего мы сейчас не делаем

Текущий workflow не:

- пересобирает translated ESCO layer
- пересобирает FAISS index при каждом запуске; retrieval-артефакты обновляются только когда они устарели
- использует reranker в активном path

Reranker уже был протестирован и сохранен только как отрицательный ablation-result.
