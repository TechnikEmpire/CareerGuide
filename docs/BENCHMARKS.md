# Benchmarks

Last updated: 2026-03-22

Последнее обновление: 2026-03-22

## English

### Purpose

This file defines the canonical retrieval benchmark workflow for the repo.

The goal is to measure the retrieval stack in a way that is:

- repeatable
- stage-separated
- explicit about what is FAISS latency versus model latency

### Canonical Query Set

The tracked query set lives in:

- `eval/retrieval_benchmark_queries.json`

This file is used for `dense` and `full` modes.

Pure `hnsw` mode uses stored vectors sampled from the current FAISS index so it
can measure ANN behavior without loading the query embedder or reranker.

The benchmark script does not rebuild retrieval artifacts. If artifacts are
missing or stale, run:

```bash
python -m backend.scripts.build_retrieval_index
```

### Canonical Benchmark Commands

Canonical HNSW-only CPU benchmark:

```bash
python -m backend.scripts.benchmark_retrieval
```

Dense retrieval benchmark on CPU:

```bash
python -m backend.scripts.benchmark_retrieval --mode dense
```

Canonical dense-only tuning sweep:

```bash
python -m backend.scripts.tune_dense_retrieval --output-json eval/out/dense_retrieval_tuning.json
```

For the current local operator workflow, that tuning step is also included in:

```bash
python -m backend.scripts.run_local_eval_workflow
```

Optional heavy diagnostic benchmark:

```bash
python -m backend.scripts.benchmark_retrieval --mode full --hf-home /tmp/careerguide_hf_cache
```

CPU-only is the default behavior. Use `--allow-gpu` only if you explicitly
want the heavy model-backed modes to use CUDA.

### What The Script Measures

The benchmark script can measure these stages separately:

- `faiss_hnsw_search`: pure ANN search latency on a precomputed stored vector
- `embed_query`: warm query-embedding latency
- `dense_retrieval`: query embedding plus FAISS HNSW candidate search
- `rerank_only`: reranking latency over the dense candidate pool
- `full_context`: full retrieval-context assembly used by the backend

### Interpretation

- If `faiss_hnsw_search` is small, HNSW itself is not the bottleneck.
- If `faiss_hnsw_search` is small but `dense_retrieval` is large, the query embedder is the cost.
- If `dense_retrieval` is acceptable but `rerank_only` is large, the reranker is the cost.
- If `full_context` is too large for a cheap CPU demo, the deployment profile should be adjusted before blaming FAISS or `llama.cpp`.

`llama.cpp` is not part of this benchmark. This benchmark is only for the
retrieval stack.

### Current Repo Position

The benchmark exists to separate ANN behavior from model-backed latency, not to
justify reranking by default.

The current tracked retrieval-eval outputs show that the reranker is both
expensive and harmful on the current qrels:

- `recall@20`: unchanged at `0.8611`
- `recall@10`: worse with reranking (`0.7963` dense vs `0.7222` rerank)
- `ndcg@10`: worse with reranking (`0.9304` dense vs `0.8814` rerank)
- `ndcg@20`: worse with reranking (`0.9397` dense vs `0.9048` rerank)

Because of that:

- the active runtime path is dense-only retrieval
- reranker benchmarking is diagnostic only
- the dense-only elbow has now been locked at `top_k=10`
- `candidate_pool` is not an active runtime lever while reranking stays off

One important implementation detail: when reranking is off, `candidate_pool`
does not change the final ranked list if it is only used to over-fetch and then
trim the same FAISS top-k results. The tuning script records candidate-pool
values for pipeline parity, but the main signal is the top-k sweep.

## Русский

### Назначение

Этот файл определяет канонический workflow benchmark для retrieval-части
репозитория.

Цель — измерять retrieval stack так, чтобы измерения были:

- повторяемыми
- разделенными по стадиям
- явно показывающими, где latency идет от FAISS, а где от моделей

### Канонический набор запросов

Отслеживаемый набор запросов находится в:

- `eval/retrieval_benchmark_queries.json`

Этот файл используется для режимов `dense` и `full`.

Чистый режим `hnsw` использует сохраненные vectors, sampled из текущего
FAISS-index, чтобы измерять поведение ANN без загрузки query embedder и
reranker.

Benchmark-скрипт не пересобирает retrieval-артефакты. Если артефакты
отсутствуют или устарели, выполните:

```bash
python -m backend.scripts.build_retrieval_index
```

### Канонические команды benchmark

Канонический CPU-benchmark только для HNSW:

```bash
python -m backend.scripts.benchmark_retrieval
```

Benchmark dense retrieval на CPU:

```bash
python -m backend.scripts.benchmark_retrieval --mode dense
```

Канонический dense-only tuning sweep:

```bash
python -m backend.scripts.tune_dense_retrieval --output-json eval/out/dense_retrieval_tuning.json
```

Для текущего локального operator-workflow этот tuning-шаг также входит в:

```bash
python -m backend.scripts.run_local_eval_workflow
```

Опциональный тяжелый diagnostic-benchmark:

```bash
python -m backend.scripts.benchmark_retrieval --mode full --hf-home /tmp/careerguide_hf_cache
```

CPU-only является поведением по умолчанию. Используйте `--allow-gpu` только
если вы явно хотите, чтобы тяжелые model-backed режимы использовали CUDA.

### Что измеряет скрипт

Benchmark-скрипт может отдельно измерять такие стадии:

- `faiss_hnsw_search`: чистая latency ANN-search по предвычисленному сохраненному vector
- `embed_query`: warm latency эмбеддинга запроса
- `dense_retrieval`: эмбеддинг запроса плюс FAISS HNSW candidate-search
- `rerank_only`: latency reranking по dense candidate pool
- `full_context`: полная сборка retrieval-context, которую использует backend

### Интерпретация

- Если `faiss_hnsw_search` маленький, значит сам HNSW не является bottleneck.
- Если `faiss_hnsw_search` маленький, а `dense_retrieval` большой, значит дорогой этап — query embedder.
- Если `dense_retrieval` приемлем, а `rerank_only` большой, значит дорогой этап — reranker.
- Если `full_context` слишком велик для дешевого CPU-demo, deployment-profile нужно настраивать до того, как обвинять FAISS или `llama.cpp`.

`llama.cpp` не входит в этот benchmark. Этот benchmark относится только к
retrieval stack.

### Текущая позиция репозитория

Benchmark нужен для отделения поведения ANN от model-backed latency, а не для
того, чтобы по умолчанию оправдывать reranking.

Текущие отслеживаемые retrieval-eval outputs показывают, что reranker и дорог,
и вреден на текущих qrels:

- `recall@20`: без изменений, `0.8611`
- `recall@10`: хуже с reranking (`0.7963` dense vs `0.7222` rerank)
- `ndcg@10`: хуже с reranking (`0.9304` dense vs `0.8814` rerank)
- `ndcg@20`: хуже с reranking (`0.9397` dense vs `0.9048` rerank)

Из этого следует:

- активный runtime-path использует dense-only retrieval
- benchmark reranker нужен только для диагностики
- dense-only elbow теперь зафиксирован на `top_k=10`
- `candidate_pool` не является активным runtime-рычагом, пока reranking остается выключенным

Одна важная деталь реализации: когда reranking выключен, `candidate_pool` не
меняет итоговый ranked list, если он используется только для over-fetch и
последующего trim тех же FAISS top-k результатов. Tuning-скрипт сохраняет
значения candidate-pool для parity с pipeline, но основной сигнал дает именно
sweep по top-k.
