# Project Status

Last updated: 2026-03-22

Последнее обновление: 2026-03-22

## English

### Current Phase

Foundational scaffold plus tracked ESCO source artifacts, a Qwen3-targeted
FAISS-backed dense retrieval stack, a validated end-to-end baseline RAG path,
and the first real persistent-memory slice now wired into the live answer flow.

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
- Repo-local embedding paths no longer invalidate retrieval artifacts by themselves; the tracked retrieval metadata now uses a stable logical model ID for `Qwen/Qwen3-Embedding-0.6B`.
- The canonical benchmark baseline is now CPU-only HNSW search over already-built retrieval artifacts.
- Canonical evaluation fixtures now exist in `eval/retrieval_qrels.json` and `eval/answer_eval_cases.json`.
- Canonical persisted retrieval-eval outputs now exist in `eval/out/`.
- The current dense-versus-reranker ablation has been run and persisted.
- The measured result is negative for reranking on the current tracked qrels, so reranking is disabled by default and is not part of the active runtime path.
- The dense-only tuning curve now justifies locking the active runtime default at `top_k=10`.
- Because reranking is disabled, `candidate_pool` no longer changes the active dense-only runtime path and remains only as an explicit ablation knob.
- The real generation client is now wired against an OpenAI-compatible local server at `/v1/chat/completions` for `Qwen/Qwen3-0.6B`.
- The preferred local generator runtime is now `llama-cpp-python[server]`, not a hand-built `llama-server` binary.
- Canonical convenience scripts now exist for repo-local model setup, one-command local app-stack startup, advanced manual runtime control, and the dense-only local evaluation workflow.
- The canonical local evaluation workflow now auto-refreshes retrieval artifacts before generation when local SQLite rows or FAISS metadata are stale.
- A canonical dense-only tuning script now exists at `python -m backend.scripts.tune_dense_retrieval`.
- A canonical answer-export script now exists at `python -m backend.scripts.export_answer_predictions`.
- The default memory store is now backed by the local SQLite `memory_items` table rather than an in-process dictionary.
- The live `/chat/answer` flow now extracts heuristic user-constraint memory candidates and persists them before retrieval and prompt assembly.
- The current memory dedupe rule is normalized-text uniqueness per user, so repeated stable phrasing does not create duplicate rows.

### Current Completion Boundary

The next clean project boundary is:

- `Memory Layer v1 Integrated`

That boundary should only be considered closed when all of these are true:

1. persistent memory storage is stable and inspectable through the active local app flow
2. the live answer path writes extracted memory before retrieval/prompt assembly
3. Hopfield-style memory summary uses persisted memory in the production path
4. `RAG-only` versus `RAG + memory` comparison outputs exist and are tracked
5. the memory-enabled evaluation outputs and repo docs reflect that stable state

Current status against that boundary:

- `1` true for the current SQLite-backed scope
- `2` true
- `3` true for the current heuristic memory scope
- `4` false
- `5` false

Boundary result:

- `Memory Layer v1 Integrated` is not closed yet.

### What Is In Progress

- Persistent memory implementation beyond the old in-process scaffold.
- Extending the evaluation harness from baseline RAG validation into `RAG-only` versus `RAG + memory` comparison.
- Broadening memory extraction and consolidation beyond the current first-pass heuristic.

### What Is Not Done Yet

- Editable user profile and artifact memory persistence
- Confirmation, archive, and supersede flow for uncertain or outdated memory
- Richer memory extraction and consolidation beyond the current first-pass heuristic
- Joint `RAG-only` versus `RAG + memory` evaluation
- Full safety-policy implementation
- Full experiment harness and report-ready result exports

### Immediate Next Steps

1. Add canonical `RAG-only` versus `RAG + memory` evaluation outputs.
2. Promote the current heuristic memory write path into a richer extraction/consolidation flow.
3. Add explicit profile/artifact memory editing and lifecycle controls.
4. Add memory-focused debug artifacts so the associative-read behavior is inspectable.

### Current Risks and Notes

- The reranker question is no longer open for the current retrieval configuration. The tracked qrels show that reranking hurts ranking quality while adding substantial runtime cost, so it should stay off by default unless the corpus, qrels, or model stack changes materially.
- The current dense baseline is good enough to move forward. The measured retrieval elbow is locked at `top_k=10`, explicit citations are now working, and the baseline answer-eval export is no longer degenerate.
- Answer quality is baseline-acceptable, not polished. Some responses are still terse or stylistically rough, so future prompt work should be evidence-driven rather than assumed complete.
- The current local workflow now assumes repo-local model caching for both the generator and the retrieval query embedder. If those local artifacts are missing, the runtime may fall back to Hugging Face resolution and surprise the operator.
- The memory layer is now real but still narrow. It persists stable heuristic user constraints, but it does not yet have confirmation flow, archival semantics, or a proper comparison report against the RAG-only baseline.
- ESCO CSV files contain multiline quoted fields, so raw line counts are not reliable record counts. Parsing must use a proper CSV reader.
- Smoke tests still force deterministic retrieval providers so they remain fast and independent of model downloads. Production defaults point at Qwen3.
- The real generation path is now wired, but the prompt design and scored answer behavior are still early-stage and need empirical iteration.
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
  - active dense-only default=`top_k=10`
  - reranker disabled by default
- Generation backend:
  - runtime=`llama-cpp-python`
  - model=`Qwen/Qwen3-0.6B`
  - artifact=`Qwen/Qwen3-0.6B-GGUF:Q8_0`
  - client wired to `/v1/chat/completions`
- Memory backend:
  - store=`SQLite memory_items table`
  - live write path=`/chat/answer` extracts and upserts heuristic user-constraint memory
  - dedupe rule=`normalized text per user`
  - prompt path=`persisted memory is summarized through the existing Hopfield-style read helper`
- Retrieval cache artifacts tracked in git:
  - `data/processed/retrieval/faiss_hnsw.index`
  - `data/processed/retrieval/faiss_hnsw_manifest.json`
- Canonical scored retrieval outputs tracked in git:
  - `eval/out/retrieval_predictions_dense.json`
  - `eval/out/retrieval_predictions_rerank.json`
  - `eval/out/retrieval_scores_dense.json`
  - `eval/out/retrieval_scores_rerank.json`
- Canonical current local evaluation outputs:
  - `eval/out/dense_retrieval_tuning.json`
  - `eval/out/answer_predictions.json`
  - `eval/out/answer_scores.json`
- Current measured retrieval outcome on tracked qrels:
  - `recall@20`: dense=`0.8611`, rerank=`0.8611`
  - `recall@10`: dense=`0.7963`, rerank=`0.7222`
  - `ndcg@10`: dense=`0.9304`, rerank=`0.8814`
  - `ndcg@20`: dense=`0.9397`, rerank=`0.9048`
- Interpretation:
  - reranking does not improve final recall on the current qrels
  - reranking degrades ranking quality at mid and high cutoffs
  - reranking is therefore not part of the active baseline
  - the dense-only elbow is `top_k=10`, which is now the active runtime default
  - `candidate_pool` is inactive in the live dense-only path while reranking remains off
- Current answer-eval state after the explicit-citation fix:
  - `answer_scores.json` aggregate evidence precision=`0.75`
  - `answer_scores.json` aggregate evidence recall=`0.5833`
  - `answer_scores.json` aggregate evidence f1=`0.6389`
  - all 6 evaluated answers now export non-empty cited chunk IDs
  - interpretation: the baseline answer export is now structurally valid and good enough to close the baseline RAG milestone

## Русский

### Текущая фаза

Базовый scaffold плюс отслеживаемые ESCO source-артефакты, dense retrieval
stack на базе FAISS для Qwen3, валидированный end-to-end baseline RAG path и
теперь уже первый реальный slice persistent-memory, подключенный к live answer
flow.

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
- Repo-local пути embedding-модели больше сами по себе не делают retrieval-артефакты устаревшими; отслеживаемая retrieval-metadata теперь использует стабильный логический model ID для `Qwen/Qwen3-Embedding-0.6B`.
- Канонический benchmark baseline теперь является CPU-only HNSW-search по уже собранным retrieval-артефактам.
- Канонические evaluation-fixtures теперь существуют в `eval/retrieval_qrels.json` и `eval/answer_eval_cases.json`.
- Канонические persisted retrieval-eval outputs теперь существуют в `eval/out/`.
- Текущая ablation dense-versus-reranker уже выполнена и зафиксирована.
- Измеренный результат для reranking на текущих отслеживаемых qrels отрицательный, поэтому reranking отключен по умолчанию и не является частью активного runtime-path.
- Dense-only tuning-кривая теперь позволяет зафиксировать активный runtime-default на `top_k=10`.
- Поскольку reranking выключен, `candidate_pool` больше не меняет активный dense-only runtime-path и остается только явным ablation-переключателем.
- Реальный generation-client теперь подключен к локальному OpenAI-compatible path `/v1/chat/completions` для `Qwen/Qwen3-0.6B`.
- Предпочтительный локальный runtime генератора теперь - `llama-cpp-python[server]`, а не вручную собранный бинарник `llama-server`.
- Теперь также существуют канонические convenience-скрипты для repo-local setup моделей, запуска локального app-stack одной командой, advanced manual control runtime и dense-only local evaluation-workflow.
- Канонический local evaluation-workflow теперь автоматически обновляет retrieval-артефакты перед generation, если локальные SQLite-rows или FAISS-metadata устарели.
- Теперь существует канонический dense-only tuning-скрипт: `python -m backend.scripts.tune_dense_retrieval`.
- Теперь существует канонический answer-export скрипт: `python -m backend.scripts.export_answer_predictions`.
- Default memory store теперь работает через локальную SQLite-таблицу `memory_items`, а не через in-process dictionary.
- Live-flow `/chat/answer` теперь извлекает heuristic memory-candidates для user-constraints и сохраняет их до retrieval и prompt assembly.
- Текущее правило дедупликации memory — уникальность normalized-text отдельно для каждого пользователя.

### Текущая граница завершения

Следующая чистая граница проекта называется:

- `Memory Layer v1 Integrated`

Эту границу можно считать закрытой только тогда, когда одновременно выполнены все условия:

1. persistent-memory storage стабилен и inspectable через активный локальный app-flow
2. live answer-path записывает extracted memory до retrieval/prompt assembly
3. Hopfield-style memory summary использует persisted memory в production-path
4. существуют и отслеживаются outputs для сравнения `RAG-only` и `RAG + memory`
5. memory-enabled evaluation-output и документация репозитория отражают это состояние

Текущий статус относительно этой границы:

- `1` выполнен для текущего SQLite-backed scope
- `2` выполнен
- `3` выполнен для текущего heuristic memory-scope
- `4` не выполнен
- `5` не выполнен

Результат по границе:

- `Memory Layer v1 Integrated` пока не закрыт.

### Что сейчас в работе

- Реализация persistent memory поверх прежнего in-process scaffold.
- Расширение evaluation harness от baseline RAG validation к сравнению `RAG-only` и `RAG + memory`.
- Расширение extraction и consolidation памяти за пределы текущей первой эвристики.

### Что еще не сделано

- Редактируемое persistent storage для user profile и artifact memory
- Confirmation/archive/supersede flow для uncertain или устаревшей memory
- Более богатые extraction и consolidation памяти за пределами текущей первой эвристики
- Совместная evaluation `RAG-only` против `RAG + memory`
- Полноценная реализация safety policy
- Полноценный experiment harness и report-ready экспорт результатов

### Ближайшие шаги

1. Добавить канонические outputs для сравнения `RAG-only` и `RAG + memory`.
2. Развить текущий heuristic memory write-path в более богатый flow extraction/consolidation.
3. Добавить явное редактирование profile/artifact memory и lifecycle-controls.
4. Добавить memory-focused debug artifacts, чтобы associative-read был inspectable.

### Текущие риски и заметки

- Вопрос о reranker для текущей retrieval-конфигурации больше не является открытым. Отслеживаемые qrels показывают, что reranking ухудшает ranking quality и одновременно добавляет заметную runtime-стоимость, поэтому по умолчанию он должен оставаться выключенным, если только корпус, qrels или model stack существенно не изменятся.
- Текущий dense baseline уже достаточно хорош, чтобы двигаться дальше. Retrieval-elbow зафиксирован на `top_k=10`, explicit citations работают, а baseline answer-eval export больше не является вырожденным.
- Качество ответов уже приемлемо для baseline, но еще не отполировано. Некоторые ответы все еще слишком краткие или стилистически грубые, поэтому будущая prompt-доработка должна быть опираться на evidence, а не на ощущения.
- Текущий локальный workflow теперь предполагает repo-local model caching и для generator, и для retrieval query-embedder. Если эти локальные артефакты отсутствуют, runtime может неожиданно обратиться к Hugging Face.
- Memory-layer теперь уже реален, но все еще узок. Он сохраняет стабильные heuristic user-constraints, но у него пока нет confirmation-flow, archival semantics и полноценного comparison-report против RAG-only baseline.
- ESCO CSV-файлы содержат multiline quoted fields, поэтому raw line counts не являются надежными record counts. Для разбора нужен полноценный CSV reader.
- Smoke-тесты по-прежнему принудительно используют deterministic retrieval providers, чтобы оставаться быстрыми и независимыми от загрузки моделей. Production-default уже указывает на Qwen3.
- Реальный generation-path уже подключен, но prompt design и scored-поведение ответов все еще находятся на ранней стадии и требуют эмпирической доработки.
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
  - active dense-only default=`top_k=10`
  - reranker отключен по умолчанию
- Generation backend:
  - runtime=`llama-cpp-python`
  - model=`Qwen/Qwen3-0.6B`
  - artifact=`Qwen/Qwen3-0.6B-GGUF:Q8_0`
  - client подключен к `/v1/chat/completions`
- Memory backend:
  - store=`SQLite memory_items table`
  - live write path=`/chat/answer` извлекает и upsert-ит heuristic user-constraint memory
  - dedupe rule=`normalized text per user`
  - prompt path=`persisted memory суммируется через существующий Hopfield-style read helper`
- Retrieval cache-артефакты, отслеживаемые в git:
  - `data/processed/retrieval/faiss_hnsw.index`
  - `data/processed/retrieval/faiss_hnsw_manifest.json`
- Канонические scored retrieval outputs, отслеживаемые в git:
  - `eval/out/retrieval_predictions_dense.json`
  - `eval/out/retrieval_predictions_rerank.json`
  - `eval/out/retrieval_scores_dense.json`
  - `eval/out/retrieval_scores_rerank.json`
- Канонические текущие output локальной evaluation:
  - `eval/out/dense_retrieval_tuning.json`
  - `eval/out/answer_predictions.json`
  - `eval/out/answer_scores.json`
- Текущий измеренный retrieval-result на отслеживаемых qrels:
  - `recall@20`: dense=`0.8611`, rerank=`0.8611`
  - `recall@10`: dense=`0.7963`, rerank=`0.7222`
  - `ndcg@10`: dense=`0.9304`, rerank=`0.8814`
  - `ndcg@20`: dense=`0.9397`, rerank=`0.9048`
- Интерпретация:
  - reranking не улучшает итоговый recall на текущих qrels
  - reranking ухудшает ranking quality на средних и высоких cutoff
  - поэтому reranking не входит в активный baseline
  - dense-only elbow находится на `top_k=10`, и это теперь активный runtime-default
  - `candidate_pool` неактивен в live dense-only path, пока reranking остается выключенным
- Текущее состояние answer-eval после исправления explicit-citation path:
  - aggregate evidence precision в `answer_scores.json` = `0.75`
  - aggregate evidence recall в `answer_scores.json` = `0.5833`
  - aggregate evidence f1 в `answer_scores.json` = `0.6389`
  - все 6 оцененных ответов теперь экспортируют непустые cited chunk IDs
  - интерпретация: baseline answer-export теперь структурно валиден и этого достаточно, чтобы закрыть baseline RAG milestone
