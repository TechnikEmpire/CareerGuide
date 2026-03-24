# Evaluation Outputs


Последнее обновление: 2026-03-22

Этот каталог хранит канонические persisted evaluation-output для текущей
отслеживаемой retrieval-конфигурации.

Отслеживаемые файлы:

- `dense_retrieval_tuning.json`
- `answer_predictions.json`
- `answer_scores.json`
- `retrieval_predictions_dense.json`
- `retrieval_predictions_rerank.json`
- `retrieval_scores_dense.json`
- `retrieval_scores_rerank.json`

Эти файлы намеренно отслеживаются, потому что они фиксируют текущее scored
состояние:

- persisted FAISS HNSW index
- активной embedding-модели
- активных настроек candidate-pool и top-k
- текущего dense-only tuning-result
- текущего export и scored-состояния answer-evaluation
- результата сравнения dense baseline и reranker ablation

Dense-файлы представляют активный runtime-baseline.

Файлы reranker сохраняются, потому что они документируют текущий отрицательный
результат ablation: reranking дороже по runtime и показывает худший результат
на отслеживаемых qrels, поэтому по умолчанию не используется.

Другие ad hoc evaluation-output должны оставаться неотслеживаемыми, если они
не были явно повышены до канонических артефактов репозитория.

Канонический локальный workflow, который производит текущие dense tuning- и
answer-файлы, такой:

```bash
python -m backend.scripts.run_local_eval_workflow
```

Этот wrapper теперь также чинит устаревшие retrieval-артефакты до generation.
Answer-файлы считаются каноническими только тогда, когда они получены через
explicit citation-path, экспортирующий model-selected `cited_chunk_ids`.
Старые answer-export, созданные до этого исправления, нужно заменять, а не
сравнивать с новыми.
