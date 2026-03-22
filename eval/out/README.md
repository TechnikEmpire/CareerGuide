# Evaluation Outputs

Last updated: 2026-03-22

Последнее обновление: 2026-03-22

## English

This directory stores the canonical persisted evaluation outputs for the
currently tracked retrieval configuration.

Tracked files:

- `retrieval_predictions_dense.json`
- `retrieval_predictions_rerank.json`
- `retrieval_scores_dense.json`
- `retrieval_scores_rerank.json`

These files are intentionally tracked because they document the current scored
state of:

- the persisted FAISS HNSW index
- the active embedding model
- the active candidate-pool and top-k settings
- the dense baseline versus reranker ablation outcome

The dense files represent the active runtime baseline.

The reranker files are retained because they document the current negative
ablation result: reranking is more expensive and performs worse on the tracked
qrels, so it is not used by default.

Other ad hoc evaluation outputs should remain untracked unless they are promoted
to canonical repo artifacts.

## Русский

Этот каталог хранит канонические persisted evaluation-output для текущей
отслеживаемой retrieval-конфигурации.

Отслеживаемые файлы:

- `retrieval_predictions_dense.json`
- `retrieval_predictions_rerank.json`
- `retrieval_scores_dense.json`
- `retrieval_scores_rerank.json`

Эти файлы намеренно отслеживаются, потому что они фиксируют текущее scored
состояние:

- persisted FAISS HNSW index
- активной embedding-модели
- активных настроек candidate-pool и top-k
- результата сравнения dense baseline и reranker ablation

Dense-файлы представляют активный runtime-baseline.

Файлы reranker сохраняются, потому что они документируют текущий отрицательный
результат ablation: reranking дороже по runtime и показывает худший результат
на отслеживаемых qrels, поэтому по умолчанию не используется.

Другие ad hoc evaluation-output должны оставаться неотслеживаемыми, если они
не были явно повышены до канонических артефактов репозитория.
