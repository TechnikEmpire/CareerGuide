# Evaluation Outputs

Last updated: 2026-03-22

This directory stores the canonical persisted evaluation outputs for the
currently tracked retrieval configuration.

Tracked files:

- `dense_retrieval_tuning.json`
- `answer_predictions.json`
- `answer_scores.json`
- `retrieval_predictions_dense.json`
- `retrieval_predictions_rerank.json`
- `retrieval_scores_dense.json`
- `retrieval_scores_rerank.json`

These files are intentionally tracked because they document the current scored
state of:

- the persisted FAISS HNSW index
- the active embedding model
- the active candidate-pool and top-k settings
- the current dense-only tuning result
- the current generated answer-evaluation export and score state
- the dense baseline versus reranker ablation outcome

The dense files represent the active runtime baseline.

The reranker files are retained because they document the current negative
ablation result: reranking is more expensive and performs worse on the tracked
qrels, so it is not used by default.

Other ad hoc evaluation outputs should remain untracked unless they are promoted
to canonical repo artifacts.

The canonical local workflow that produces the current dense tuning plus answer
files is:

```bash
python -m backend.scripts.run_local_eval_workflow
```

That wrapper now also repairs stale retrieval artifacts before generation.
The answer files are only canonical when they were produced by the explicit
citation path that exports model-selected `cited_chunk_ids`. Older answer
exports created before that fix should be replaced, not compared.
