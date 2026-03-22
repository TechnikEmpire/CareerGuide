# Evaluation

Last updated: 2026-03-22

Последнее обновление: 2026-03-22

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

### Canonical Simple RAG Baseline

The minimal RAG baseline for this repo is:

- `Qwen/Qwen3-Embedding-0.6B`
- FAISS HNSW ANN retrieval
- top-k context selection
- `Qwen/Qwen3-0.6B` via `llama.cpp`

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

These can be scored with:

```bash
python -m backend.scripts.export_retrieval_predictions --output-json eval/out/retrieval_predictions_dense.json
python -m eval.score_eval --retrieval-predictions eval/out/retrieval_predictions_dense.json --output-json eval/out/retrieval_scores_dense.json

python -m eval.score_eval --answer-predictions /path/to/answer_predictions.json
```

Reranker exports are retained as a scored ablation record, not as the active
runtime recommendation:

```bash
python -m backend.scripts.export_retrieval_predictions --use-reranker --output-json eval/out/retrieval_predictions_rerank.json
python -m eval.score_eval --retrieval-predictions eval/out/retrieval_predictions_rerank.json --output-json eval/out/retrieval_scores_rerank.json
```

### Canonical Persisted Eval Outputs

The repo treats these four outputs as the canonical persisted retrieval-eval
state:

- `eval/out/retrieval_predictions_dense.json`
- `eval/out/retrieval_predictions_rerank.json`
- `eval/out/retrieval_scores_dense.json`
- `eval/out/retrieval_scores_rerank.json`

The dense files document the active runtime baseline.

The reranker files are intentionally retained because they document the current
negative ablation result against the same tracked qrels.

### Canonical Basis

This evaluation policy is grounded in:

- the original RAG formulation by Lewis et al. (retrieval followed by generation): `https://arxiv.org/abs/2005.11401`
- BEIR for retrieval-style metrics such as `nDCG`, `Recall`, and `MRR`: `https://arxiv.org/abs/2104.08663`
- RAGAS for automated RAG evaluation dimensions and workflow ideas: `https://arxiv.org/abs/2309.15217`

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

### Канонический простой baseline RAG

Минимальный RAG baseline для этого репозитория:

- `Qwen/Qwen3-Embedding-0.6B`
- FAISS HNSW ANN retrieval
- выбор top-k context
- `Qwen/Qwen3-0.6B` через `llama.cpp`

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

Их можно score-ить так:

```bash
python -m backend.scripts.export_retrieval_predictions --output-json eval/out/retrieval_predictions_dense.json
python -m eval.score_eval --retrieval-predictions eval/out/retrieval_predictions_dense.json --output-json eval/out/retrieval_scores_dense.json

python -m eval.score_eval --answer-predictions /path/to/answer_predictions.json
```

Экспорты reranker сохраняются как зафиксированный ablation-result, а не как
активная runtime-рекомендация:

```bash
python -m backend.scripts.export_retrieval_predictions --use-reranker --output-json eval/out/retrieval_predictions_rerank.json
python -m eval.score_eval --retrieval-predictions eval/out/retrieval_predictions_rerank.json --output-json eval/out/retrieval_scores_rerank.json
```

### Канонические persisted evaluation-output

Репозиторий рассматривает следующие четыре файла как каноническое persisted
состояние retrieval-eval:

- `eval/out/retrieval_predictions_dense.json`
- `eval/out/retrieval_predictions_rerank.json`
- `eval/out/retrieval_scores_dense.json`
- `eval/out/retrieval_scores_rerank.json`

Dense-файлы документируют активный runtime-baseline.

Файлы reranker намеренно сохраняются, потому что они фиксируют текущий
отрицательный ablation-result на тех же отслеживаемых qrels.

### Каноническая основа

Эта политика evaluation основана на:

- исходной формулировке RAG у Lewis et al. (retrieval, а затем generation): `https://arxiv.org/abs/2005.11401`
- BEIR для retrieval-метрик вроде `nDCG`, `Recall` и `MRR`: `https://arxiv.org/abs/2104.08663`
- RAGAS для dimensions автоматической оценки RAG и идей workflow: `https://arxiv.org/abs/2309.15217`
