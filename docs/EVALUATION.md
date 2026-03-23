# Evaluation

Last updated: 2026-03-23

Последнее обновление: 2026-03-23

## English

### Current Position

The reranker has now been tested on the tracked retrieval qrels, and the
current result is negative.

The active retrieval baseline for this repo is therefore:

1. chunk corpus
2. embed corpus
3. ANN retrieval
4. grounded generation

Reranking is not part of the active baseline. It remains only as a retained
negative ablation result and as a future regression check if the corpus, qrels,
or model stack changes materially.

### Current Measured Retrieval Outcome

The canonical scored outputs in `eval/out/` currently show:

- `recall@20`: dense=`0.8611`, rerank=`0.8611`
- `recall@10`: dense=`0.7963`, rerank=`0.7222`
- `ndcg@10`: dense=`0.9304`, rerank=`0.8814`
- `ndcg@20`: dense=`0.9397`, rerank=`0.9048`

Interpretation:

- the reranker does not improve final recall on the current qrels
- the reranker degrades ranking quality at important cutoffs
- the reranker also adds substantial runtime cost
- the repo should therefore use dense-only retrieval by default
- the best current dense-only tradeoff is the elbow at `top_k=10`
- `candidate_pool` is not part of the active dense-only runtime decision while reranking stays off

### Canonical Simple RAG Baseline

The minimal RAG baseline for this repo is:

- `Qwen/Qwen3-Embedding-0.6B`
- FAISS HNSW ANN retrieval
- top-k context selection
- `Qwen/Qwen3-0.6B` via a local OpenAI-compatible GGUF server, with `llama-cpp-python[server]` as the preferred local runtime

This is the baseline that should be optimized first and evaluated honestly.

### Canonical Retrieval Evaluation

For retrieval quality, use IR-style metrics over labeled relevant chunks.

The core metrics are:

- `Recall@k`
- `MRR@k`
- `nDCG@k`

These metrics are what determine:

- whether top-5, top-10, or top-20 makes sense
- whether dense-only retrieval is already sufficient
- whether any future reranking change is actually justified

### Canonical Answer Evaluation

For answer quality, do not rely only on qualitative impressions.

The answer-evaluation axes remain:

- context relevance
- answer faithfulness
- answer relevance

For this academic repo, the defensible stack is:

1. retrieval metrics over labeled relevant chunks
2. answer-level evaluation on fixed scenario sets
3. faithfulness-focused judging or scoring for groundedness
4. explicit ablations only when they are worth measuring

The answer-evidence score is only meaningful if `cited_chunk_ids` reflect
explicit model-selected citations. Treating the entire retrieved context as if
all chunks were cited is not canonical, because it turns evidence precision
into a proxy for context width rather than attribution quality.

### Canonical Memory Evaluation

The core memory comparison for this repo is:

1. `RAG-only`
2. `RAG + naive memory retrieval`
3. `RAG + Hopfield top1 recall`
4. `RAG + Hopfield topk recall`

The current implementation already supports the Hopfield recall modes needed
for arms 3 and 4, but the tracked comparison outputs are still pending.

The active shipped Hopfield phase is intentionally the simplest defensible one:

- real embedding-space memory vectors
- non-trainable one-step Hopfield recall
- `top1` sharp single-memory selection
- `topk` exact top-k masking plus renormalization over softmax weights

This is grounded in Davydov, Jaffe, Singh, and Bullo, "Retrieving k-Nearest
Memories with Modern Hopfield Networks", committed in the repo at
`docs/papers/33_Retrieving_k_Nearest_Memori.pdf` and
`docs/papers/hopfield_memory.txt`.

### Current Canonical Eval Fixtures

The repo tracks these canonical evaluation artifacts:

- `eval/retrieval_benchmark_queries.json`
- `eval/retrieval_qrels.json`
- `eval/answer_eval_cases.json`

The retrieval qrels file is the canonical source for:

- `Recall@k`
- `MRR@k`
- `nDCG@k`

The answer-evaluation cases file is the canonical source for:

- expected evidence chunk IDs
- reference answer-outline expectations
- answer-level quality axes

### Canonical Prediction Formats

Retrieval predictions should be shaped like:

```json
[
  {
    "query_id": "software_developer_en",
    "ranked_chunk_ids": [
      "esco:http://data.europa.eu/esco/occupation/f2b15a0e-e65a-438a-affb-29b9d50b77d1"
    ]
  }
]
```

Answer-evidence predictions should be shaped like:

```json
[
  {
    "case_id": "career-transition-en-001",
    "cited_chunk_ids": [
      "esco:http://data.europa.eu/esco/occupation/60082a99-d8ef-4e84-9290-78902681b6ed"
    ]
  }
]
```

If older answer exports were created before the explicit-citation fix, discard
them and regenerate them. They are not comparable to the current canonical
answer-evidence metric.

The canonical export format still uses chunk IDs. Internally, the generator may
emit shorter numbered evidence references, and the application normalizes those
refs back into canonical `cited_chunk_ids` during export.

These can be scored with:

```bash
python -m backend.scripts.export_retrieval_predictions --output-json eval/out/retrieval_predictions_dense.json
python -m eval.score_eval --retrieval-predictions eval/out/retrieval_predictions_dense.json --output-json eval/out/retrieval_scores_dense.json

python -m backend.scripts.export_answer_predictions --output-json eval/out/answer_predictions.json
python -m eval.score_eval --answer-predictions eval/out/answer_predictions.json --output-json eval/out/answer_scores.json
```

For the current local operator workflow, the dense-only tuning plus
answer-generation scoring path is usually run through:

```bash
python -m backend.scripts.run_local_eval_workflow
```

That wrapper does not replace the canonical files or metrics. It just runs the
same canonical dense-only tuning and answer-eval commands in sequence.
It also validates the retrieval artifacts first and refreshes them automatically
if the local SQLite rows or FAISS metadata are stale.

Reranker exports are retained as a scored ablation record, not as the active
runtime recommendation:

```bash
python -m backend.scripts.export_retrieval_predictions --use-reranker --output-json eval/out/retrieval_predictions_rerank.json
python -m eval.score_eval --retrieval-predictions eval/out/retrieval_predictions_rerank.json --output-json eval/out/retrieval_scores_rerank.json
```

### Canonical Persisted Eval Outputs

The repo treats these outputs as the canonical persisted retrieval-eval state:

- `eval/out/retrieval_predictions_dense.json`
- `eval/out/retrieval_predictions_rerank.json`
- `eval/out/retrieval_scores_dense.json`
- `eval/out/retrieval_scores_rerank.json`
- `eval/out/answer_predictions.json`
- `eval/out/answer_scores.json`

The dense files document the active runtime baseline.

The reranker files are intentionally retained because they document the current
negative ablation result against the same tracked qrels.

The answer files document the current generated-answer export and the current
automated evidence-overlap score state.
They should be regenerated whenever citation-attribution logic changes, because
the metric depends on explicit model-selected `cited_chunk_ids`.

The local model runtime needed for those files is not tracked in Git. The
canonical repo-local model cache lives under `models/` and is populated by:

```bash
python -m backend.scripts.setup_local_models
```

### Canonical Basis

This evaluation policy is grounded in:

- the original RAG formulation by Lewis et al. (retrieval followed by generation): `https://arxiv.org/abs/2005.11401`
- BEIR for retrieval-style metrics such as `nDCG`, `Recall`, and `MRR`: `https://arxiv.org/abs/2104.08663`
- RAGAS for automated RAG evaluation dimensions and workflow ideas: `https://arxiv.org/abs/2309.15217`
- Davydov, Jaffe, Singh, and Bullo for modern Hopfield `top1` versus `topk` memory retrieval framing: `docs/papers/33_Retrieving_k_Nearest_Memori.pdf`

## Русский

### Текущая позиция

Reranker уже протестирован на отслеживаемых retrieval qrels, и текущий
результат отрицательный.

Поэтому активный retrieval-baseline для этого репозитория теперь такой:

1. chunk-ing корпуса
2. embedding корпуса
3. ANN retrieval
4. grounded generation

Reranking больше не является частью активного baseline. Он сохраняется только
как зафиксированный отрицательный ablation-result и как возможная future
regression-check, если существенно изменятся корпус, qrels или model stack.

### Текущий измеренный результат retrieval

Канонические scored-output в `eval/out/` сейчас показывают:

- `recall@20`: dense=`0.8611`, rerank=`0.8611`
- `recall@10`: dense=`0.7963`, rerank=`0.7222`
- `ndcg@10`: dense=`0.9304`, rerank=`0.8814`
- `ndcg@20`: dense=`0.9397`, rerank=`0.9048`

Интерпретация:

- reranker не улучшает итоговый recall на текущих qrels
- reranker ухудшает ranking quality на важных cutoff
- reranker также добавляет заметную runtime-стоимость
- поэтому репозиторий должен использовать dense-only retrieval по умолчанию
- лучшая текущая dense-only tradeoff-точка — elbow на `top_k=10`
- `candidate_pool` не является частью активного dense-only runtime-решения, пока reranking выключен

### Канонический простой baseline RAG

Минимальный RAG baseline для этого репозитория:

- `Qwen/Qwen3-Embedding-0.6B`
- FAISS HNSW ANN retrieval
- выбор top-k context
- `Qwen/Qwen3-0.6B` через локальный OpenAI-compatible GGUF-server, где `llama-cpp-python[server]` является предпочтительным локальным runtime

Именно этот baseline нужно сначала оптимизировать и честно оценивать.

### Каноническая evaluation retrieval

Для качества retrieval используйте IR-метрики по размеченным relevant
chunk-ам.

Основные метрики:

- `Recall@k`
- `MRR@k`
- `nDCG@k`

Именно они определяют:

- имеет ли смысл top-5, top-10 или top-20
- достаточно ли хорош dense-only retrieval
- оправдано ли вообще любое будущее изменение reranking

### Каноническая evaluation ответов

Для оценки качества ответов нельзя полагаться только на качественные
впечатления.

Оси оценки ответов остаются такими:

- context relevance
- answer faithfulness
- answer relevance

Для этого академического репозитория защищаемый stack выглядит так:

1. retrieval-метрики по размеченным relevant chunk-ам
2. answer-level evaluation на фиксированных наборах сценариев
3. judging или scoring, сфокусированный на faithfulness и groundedness
4. явные ablation-эксперименты только там, где их действительно стоит измерять

Score для answer-evidence имеет смысл только тогда, когда `cited_chunk_ids`
отражают явные citation-ID, выбранные моделью. Считать цитатами весь
retrieved-context некорректно, потому что тогда precision перестает измерять
качество атрибуции и превращается в косвенную метрику ширины context.

### Каноническая evaluation memory

Основное сравнение memory для этого репозитория такое:

1. `RAG-only`
2. `RAG + naive memory retrieval`
3. `RAG + Hopfield top1 recall`
4. `RAG + Hopfield topk recall`

Текущая реализация уже поддерживает Hopfield-режимы recall, необходимые для
веток 3 и 4, но отслеживаемые comparison-output для них еще впереди.

Текущая поставляемая Hopfield-фаза намеренно является самым простым
защищаемым вариантом:

- реальные memory-векторы в embedding-space
- нетренируемый one-step Hopfield recall
- `top1` как sharp single-memory selection
- `topk` как exact top-k masking с перенормировкой softmax-весов

Этот этап опирается на работу Davydov, Jaffe, Singh и Bullo, "Retrieving
k-Nearest Memories with Modern Hopfield Networks", зафиксированную в
репозитории как `docs/papers/33_Retrieving_k_Nearest_Memori.pdf` и
`docs/papers/hopfield_memory.txt`.

### Текущие канонические evaluation-fixtures

Репозиторий отслеживает следующие канонические evaluation-артефакты:

- `eval/retrieval_benchmark_queries.json`
- `eval/retrieval_qrels.json`
- `eval/answer_eval_cases.json`

Файл retrieval qrels является каноническим источником для:

- `Recall@k`
- `MRR@k`
- `nDCG@k`

Файл answer-evaluation cases является каноническим источником для:

- expected evidence chunk IDs
- reference answer-outline expectations
- axes answer-level quality

### Канонические форматы prediction

Retrieval-predictions должны иметь вид:

```json
[
  {
    "query_id": "software_developer_en",
    "ranked_chunk_ids": [
      "esco:http://data.europa.eu/esco/occupation/f2b15a0e-e65a-438a-affb-29b9d50b77d1"
    ]
  }
]
```

Predictions для answer-evidence должны иметь вид:

```json
[
  {
    "case_id": "career-transition-en-001",
    "cited_chunk_ids": [
      "esco:http://data.europa.eu/esco/occupation/60082a99-d8ef-4e84-9290-78902681b6ed"
    ]
  }
]
```

Если старые answer-export были созданы до исправления explicit-citation path,
их нужно отбросить и перегенерировать. Они несопоставимы с текущей
канонической метрикой answer-evidence.

Канонический export-формат по-прежнему использует chunk IDs. Внутри generator
может выдавать более короткие numbered evidence refs, а приложение уже
нормализует эти refs обратно в канонические `cited_chunk_ids` при export.

Их можно score-ить так:

```bash
python -m backend.scripts.export_retrieval_predictions --output-json eval/out/retrieval_predictions_dense.json
python -m eval.score_eval --retrieval-predictions eval/out/retrieval_predictions_dense.json --output-json eval/out/retrieval_scores_dense.json

python -m backend.scripts.export_answer_predictions --output-json eval/out/answer_predictions.json
python -m eval.score_eval --answer-predictions eval/out/answer_predictions.json --output-json eval/out/answer_scores.json
```

Для текущего локального operator-workflow dense-only tuning и path
answer-generation scoring обычно запускаются через:

```bash
python -m backend.scripts.run_local_eval_workflow
```

Этот wrapper не заменяет канонические файлы или метрики. Он просто
последовательно запускает те же самые канонические dense-only tuning- и
answer-eval команды.
Он также сначала проверяет retrieval-артефакты и автоматически обновляет их,
если локальные SQLite-rows или FAISS-metadata устарели.

Экспорты reranker сохраняются как зафиксированный ablation-result, а не как
активная runtime-рекомендация:

```bash
python -m backend.scripts.export_retrieval_predictions --use-reranker --output-json eval/out/retrieval_predictions_rerank.json
python -m eval.score_eval --retrieval-predictions eval/out/retrieval_predictions_rerank.json --output-json eval/out/retrieval_scores_rerank.json
```

### Канонические persisted evaluation-output

Репозиторий рассматривает следующие файлы как каноническое persisted состояние
retrieval-eval:

- `eval/out/retrieval_predictions_dense.json`
- `eval/out/retrieval_predictions_rerank.json`
- `eval/out/retrieval_scores_dense.json`
- `eval/out/retrieval_scores_rerank.json`
- `eval/out/answer_predictions.json`
- `eval/out/answer_scores.json`

Dense-файлы документируют активный runtime-baseline.

Файлы reranker намеренно сохраняются, потому что они фиксируют текущий
отрицательный ablation-result на тех же отслеживаемых qrels.

Файлы answer документируют текущий export сгенерированных ответов и текущее
автоматизированное состояние score по overlap evidence.
Их следует перегенерировать при любом изменении логики attribution цитат,
потому что метрика зависит от explicit model-selected `cited_chunk_ids`.

Локальный model-runtime, необходимый для получения этих файлов, не
отслеживается в Git. Канонический repo-local model-cache находится в `models/`
и заполняется командой:

```bash
python -m backend.scripts.setup_local_models
```

### Каноническая основа

Эта политика evaluation основана на:

- исходной формулировке RAG у Lewis et al. (retrieval, а затем generation): `https://arxiv.org/abs/2005.11401`
- BEIR для retrieval-метрик вроде `nDCG`, `Recall` и `MRR`: `https://arxiv.org/abs/2104.08663`
- RAGAS для dimensions автоматической оценки RAG и идей workflow: `https://arxiv.org/abs/2309.15217`
- Davydov, Jaffe, Singh и Bullo для framing memory-retrieval в режимах modern Hopfield `top1` и `topk`: `docs/papers/33_Retrieving_k_Nearest_Memori.pdf`
