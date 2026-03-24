# Benchmarks


Последнее обновление: 2026-03-22

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
