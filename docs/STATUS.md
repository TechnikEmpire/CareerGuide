# Project Status

Last updated: 2026-03-22

Последнее обновление: 2026-03-22

## English

### Current Phase

Foundational scaffold plus tracked ESCO source artifacts, a Qwen3-targeted
FAISS-backed dense retrieval stack, and canonical retrieval evaluation with a
measured dense-versus-reranker outcome.

### What Is Already Done

- Bilingual authoritative repo documentation is in place.
- Canonical decision tracking is in place.
- Local setup instructions exist for WSL, Windows, and macOS.
- A Python-first backend scaffold exists with FastAPI routing and explicit service boundaries.
- The initial Hopfield-style associative-read scaffold exists.
- Standalone ESCO preprocessing and translation tooling exists under `tooling/translation/`.
- The ESCO English CSV classification dump has been normalized into the repo's common concept and relation format.
- The one-time ESCO English-to-Russian translation run has been completed and written to the tracked bilingual corpus.
- ESCO artifact tracking policy is defined: raw vendor data stays ignored, while normalized concepts, normalized relations, the bilingual translated corpus, and preprocessing manifests are tracked.
- The active retrieval path now uses SQLite for persisted ESCO chunks and metadata plus FAISS HNSW for dense ANN retrieval.
- The active dense retrieval baseline now uses `Qwen/Qwen3-Embedding-0.6B`.
- The persisted FAISS retrieval cache (`faiss_hnsw.index` and `faiss_hnsw_manifest.json`) is a tracked repo artifact.
- The retrieval build workflow is explicit: `python -m backend.scripts.build_retrieval_index`.
- The retrieval build command can restore stale SQLite retrieval rows from the tracked FAISS cache without forcing a second full corpus-embedding pass.
- The canonical benchmark baseline is now CPU-only HNSW search over already-built retrieval artifacts.
- Canonical evaluation fixtures now exist in `eval/retrieval_qrels.json` and `eval/answer_eval_cases.json`.
- Canonical persisted retrieval-eval outputs now exist in `eval/out/`.
- The current dense-versus-reranker ablation has been run and persisted.
- The measured result is negative for reranking on the current tracked qrels, so reranking is disabled by default and is not part of the active runtime path.
- The planned generator default is now `Qwen/Qwen3-0.6B` via `llama.cpp`.

### What Is In Progress

- Moving from retrieval-backed context assembly to real `llama.cpp` generation.
- Moving from retrieval-only evaluation into answer-output evaluation on generated responses.

### What Is Not Done Yet

- Full end-to-end runtime validation of the `Qwen/Qwen3-0.6B` generator path through `llama.cpp`
- Dense-only top-k and candidate-pool tuning against the tracked qrels
- Answer-level evaluation over real generated outputs
- Persistent memory storage
- Full safety-policy implementation
- Full experiment harness and report-ready result exports

### Immediate Next Steps

1. Wire the real `llama.cpp` generation client for `Qwen/Qwen3-0.6B`.
2. Run dense-only top-k and candidate-pool ablations against the tracked qrels.
3. Add answer-level scoring over real generated outputs.
4. Continue with persistent memory storage and stronger evaluation traces.

### Current Risks and Notes

- The reranker question is no longer open for the current retrieval configuration. The tracked qrels show that reranking hurts ranking quality while adding substantial runtime cost, so it should stay off by default unless the corpus, qrels, or model stack changes materially.
- The current dense baseline is good enough to move forward, but top-k and candidate-pool settings are still empirical and need a measured sweep.
- ESCO CSV files contain multiline quoted fields, so raw line counts are not reliable record counts. Parsing must use a proper CSV reader.
- Smoke tests still force deterministic retrieval providers so they remain fast and independent of model downloads. Production defaults point at Qwen3.
- The current generation behavior is still scaffold logic, not the final academic system.
- FastAPI still raises a deprecation warning for `on_event`; this is not blocking, but it should be cleaned up when the app wiring matures.

### Latest Verified State

- Tracked ESCO outputs:
  - normalized concepts=`18237`
  - normalized relations=`156336`
  - bilingual translated concepts=`18237`
- Retrieval backend:
  - SQLite-persisted ESCO chunks and metadata
  - FAISS HNSW dense ANN index
  - active embedder=`Qwen/Qwen3-Embedding-0.6B`
  - reranker disabled by default
- Retrieval cache artifacts tracked in git:
  - `data/processed/retrieval/faiss_hnsw.index`
  - `data/processed/retrieval/faiss_hnsw_manifest.json`
- Canonical scored retrieval outputs tracked in git:
  - `eval/out/retrieval_predictions_dense.json`
  - `eval/out/retrieval_predictions_rerank.json`
  - `eval/out/retrieval_scores_dense.json`
  - `eval/out/retrieval_scores_rerank.json`
- Current measured retrieval outcome on tracked qrels:
  - `recall@20`: dense=`0.8611`, rerank=`0.8611`
  - `recall@10`: dense=`0.7963`, rerank=`0.7222`
  - `ndcg@10`: dense=`0.9304`, rerank=`0.8814`
  - `ndcg@20`: dense=`0.9397`, rerank=`0.9048`
- Interpretation:
  - reranking does not improve final recall on the current qrels
  - reranking degrades ranking quality at mid and high cutoffs
  - reranking is therefore not part of the active baseline

## Русский

### Текущая фаза

Базовый scaffold плюс отслеживаемые ESCO source-артефакты, dense retrieval
stack на базе FAISS для Qwen3 и каноническая evaluation retrieval с уже
полученным измеренным результатом dense-versus-reranker.

### Что уже сделано

- Билингвальная authoritative-документация репозитория уже создана.
- Каноническое отслеживание решений уже работает.
- Есть инструкции локальной настройки для WSL, Windows и macOS.
- Существует Python-first backend scaffold с FastAPI routing и явными service boundaries.
- Есть начальный scaffold для Hopfield-style associative read.
- Существует standalone tooling для preprocessing и перевода ESCO в `tooling/translation/`.
- English CSV classification dump ESCO уже нормализован в общий формат concepts и relations репозитория.
- One-time перевод ESCO с английского на русский уже выполнен и записан в отслеживаемый bilingual corpus.
- Политика отслеживания ESCO-артефактов определена: raw vendor data игнорируется, а normalized concepts, normalized relations, bilingual translated corpus и preprocessing manifests отслеживаются.
- Активный retrieval-path теперь использует SQLite для persisted ESCO chunks и metadata и FAISS HNSW для dense ANN retrieval.
- Активный dense baseline retrieval теперь использует `Qwen/Qwen3-Embedding-0.6B`.
- Persisted FAISS retrieval cache (`faiss_hnsw.index` и `faiss_hnsw_manifest.json`) теперь является отслеживаемым артефактом репозитория.
- Workflow сборки retrieval сделан явным: `python -m backend.scripts.build_retrieval_index`.
- Команда сборки retrieval умеет восстанавливать устаревшие SQLite retrieval-rows из отслеживаемого FAISS-cache без повторного полного corpus-embedding pass.
- Канонический benchmark baseline теперь является CPU-only HNSW-search по уже собранным retrieval-артефактам.
- Канонические evaluation-fixtures теперь существуют в `eval/retrieval_qrels.json` и `eval/answer_eval_cases.json`.
- Канонические persisted retrieval-eval outputs теперь существуют в `eval/out/`.
- Текущая ablation dense-versus-reranker уже выполнена и зафиксирована.
- Измеренный результат для reranking на текущих отслеживаемых qrels отрицательный, поэтому reranking отключен по умолчанию и не является частью активного runtime-path.
- Планируемый generator-default теперь - `Qwen/Qwen3-0.6B` через `llama.cpp`.

### Что сейчас в работе

- Переход от сборки retrieval-context к реальной генерации через `llama.cpp`.
- Переход от retrieval-only evaluation к answer-output evaluation на реально сгенерированных ответах.

### Что еще не сделано

- Полная end-to-end runtime-валидация пути генератора `Qwen/Qwen3-0.6B` через `llama.cpp`
- Настройка dense-only top-k и candidate-pool по отслеживаемым qrels
- Answer-level evaluation на реальных сгенерированных ответах
- Persistent storage для памяти
- Полноценная реализация safety policy
- Полноценный experiment harness и report-ready экспорт результатов

### Ближайшие шаги

1. Подключить реальный `llama.cpp` generation client для `Qwen/Qwen3-0.6B`.
2. Выполнить dense-only ablation по top-k и candidate-pool на отслеживаемых qrels.
3. Добавить answer-level scoring на реально сгенерированных ответах.
4. Продолжить работу над persistent memory storage и более сильными evaluation traces.

### Текущие риски и заметки

- Вопрос о reranker для текущей retrieval-конфигурации больше не является открытым. Отслеживаемые qrels показывают, что reranking ухудшает ranking quality и одновременно добавляет заметную runtime-стоимость, поэтому по умолчанию он должен оставаться выключенным, если только корпус, qrels или model stack существенно не изменятся.
- Текущий dense baseline уже достаточно хорош, чтобы двигаться дальше, но настройки top-k и candidate-pool все еще остаются эмпирическими и требуют измеряемого sweep.
- ESCO CSV-файлы содержат multiline quoted fields, поэтому raw line counts не являются надежными record counts. Для разбора нужен полноценный CSV reader.
- Smoke-тесты по-прежнему принудительно используют deterministic retrieval providers, чтобы оставаться быстрыми и независимыми от загрузки моделей. Production-default уже указывает на Qwen3.
- Текущее поведение generation пока остается scaffold-логикой, а не финальной академической системой.
- FastAPI по-прежнему выдает deprecation warning для `on_event`; это не блокирует работу, но должно быть приведено в порядок по мере взросления app wiring.

### Последнее подтвержденное состояние

- Отслеживаемые ESCO outputs:
  - normalized concepts=`18237`
  - normalized relations=`156336`
  - bilingual translated concepts=`18237`
- Retrieval backend:
  - SQLite-persisted ESCO chunks и metadata
  - FAISS HNSW dense ANN index
  - active embedder=`Qwen/Qwen3-Embedding-0.6B`
  - reranker отключен по умолчанию
- Retrieval cache-артефакты, отслеживаемые в git:
  - `data/processed/retrieval/faiss_hnsw.index`
  - `data/processed/retrieval/faiss_hnsw_manifest.json`
- Канонические scored retrieval outputs, отслеживаемые в git:
  - `eval/out/retrieval_predictions_dense.json`
  - `eval/out/retrieval_predictions_rerank.json`
  - `eval/out/retrieval_scores_dense.json`
  - `eval/out/retrieval_scores_rerank.json`
- Текущий измеренный retrieval-result на отслеживаемых qrels:
  - `recall@20`: dense=`0.8611`, rerank=`0.8611`
  - `recall@10`: dense=`0.7963`, rerank=`0.7222`
  - `ndcg@10`: dense=`0.9304`, rerank=`0.8814`
  - `ndcg@20`: dense=`0.9397`, rerank=`0.9048`
- Интерпретация:
  - reranking не улучшает итоговый recall на текущих qrels
  - reranking ухудшает ranking quality на средних и высоких cutoff
  - поэтому reranking не входит в активный baseline
