# Project Status

Last updated: 2026-03-23

Последнее обновление: 2026-03-23

## English

### Current Phase

Foundational scaffold plus tracked ESCO source artifacts, a Qwen3-targeted
FAISS-backed dense retrieval stack, a validated end-to-end baseline RAG path,
the first real embedding-based Hopfield memory slice now wired into the live
answer flow, and the first real web UI slice now wired to the live backend.

### What Is Already Done

- Bilingual authoritative repo documentation is in place.
- Canonical decision tracking is in place.
- Local setup instructions exist for WSL, Windows, and macOS.
- A Python-first backend scaffold exists with FastAPI routing and explicit service boundaries.
- A basic non-trainable Hopfield memory read now exists over the real semantic embedding stack with explicit `top1` and `topk` recall modes.
- Standalone ESCO preprocessing and translation tooling exists under `tooling/translation/`.
- Standalone ru/en synthetic-data and BiLSTM training tooling for memory extraction now exists under `tooling/memory_extraction/`, using direct local-model GPU generation instead of app-server generation.
- The synthetic-data generator now rotates prompt variants, rejects repeated openings plus token-set near-duplicates, and stops collapsed buckets on consecutive no-progress attempts instead of silently stalling.
- The raw extraction corpus keeps fine-grained labels, but the first supervised extractor baseline is now binary `MEMORY` versus `NO_MEMORY` rather than five-way multiclass from the start.
- The standalone binary BiLSTM extraction baseline is now trained, evaluated, and wired into the live backend write path through sentence-level extraction.
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
- The live `/chat/answer` flow now extracts sentence-level memory candidates through the tracked binary BiLSTM bundle and persists them before retrieval and prompt assembly.
- Runtime sentence segmentation now prefers `pySBD` and falls back to regex splitting if `pysbd` is not yet installed in the app environment.
- The current memory dedupe rule is normalized-text uniqueness per user, so repeated stable phrasing does not create duplicate rows.
- The live prompt path now summarizes persisted memory through a basic non-trainable Hopfield recall step over real embedding vectors.
- Unit tests now cover the current Hopfield recall modes in `backend/tests/test_hopfield_memory.py`.
- The backend dev-server wrapper now builds reload globs as relative patterns, and that behavior is covered by `backend/tests/test_dev_server_scripts.py`.
- A lightweight React + Vite web UI now exists under `frontend/`.
- The first UI slice now covers profile selection, grounded chat, citations, “memory used”, structured plan generation, and memory inspection.
- The backend now allows standard local frontend dev origins through explicit CORS configuration.

### Current Completion Boundary

The next clean project boundary is:

- `Memory Layer v1 Integrated`

That boundary should only be considered closed when all of these are true:

1. persistent memory storage is stable and inspectable through the active local app flow
2. the live answer path writes extracted memory before retrieval/prompt assembly
3. the memory read uses a real embedding-based Hopfield mechanism with explicit `top1` and `topk` recall modes rather than a placeholder hash scaffold
4. tracked outputs exist for `RAG-only`, `RAG + naive memory`, `RAG + Hopfield top1`, and `RAG + Hopfield topk`
5. memory extraction behaves acceptably for Russian-first usage rather than only English-triggered usage
6. the memory-enabled evaluation outputs and repo docs reflect that stable state

Current status against that boundary:

- `1` true for the current SQLite-backed scope
- `2` true
- `3` true
- `4` false
- `5` false
- `6` false

Boundary result:

- `Memory Layer v1 Integrated` is not closed yet.

### What Is In Progress

- Finishing the remaining `Web UI v1` slice, especially save/reload plan flow and Russian-first polish.
- Profile and artifact memory implementation beyond the current `memory_items` slice.
- Extending the evaluation harness from baseline RAG validation into `RAG-only` versus naive-memory versus Hopfield-memory comparison.
- Measuring and calibrating the live sentence-level extractor beyond the current synthetic-only evidence.
- Adding memory-debug artifacts and comparison traces so the current Hopfield read is inspectable.
- Verifying the preferred `pySBD` runtime path in refreshed local app environments and measuring real-chat extraction quality.

### What Is Not Done Yet

These items are now explicitly **post-first-version refinements**. They are
important for later evaluation quality, thesis defensibility, and product
polish, but they are not blockers for the current first working backend plus
web-UI version.

- Editable user profile and artifact memory persistence
- Confirmation, archive, and supersede flow for uncertain or outdated memory
- Richer memory extraction and consolidation beyond the current normalized-text dedupe rule
- Tracked `RAG-only` versus naive-memory versus Hopfield-memory evaluation
- Bilingual memory detection that behaves acceptably on real chat rather than only on synthetic data
- Real-chat bilingual memory detection that is measured and acceptable beyond the current synthetic benchmark
- Later fine-grained type classification for `PREFERENCE`, `CONSTRAINT`, `GOAL`, and `AVAILABILITY`
- Memory-debug exports, comparison traces, and report-ready artifacts
- Learned projections and differentiable `ksoftmax` as a future Hopfield phase
- Structured career/wellbeing artifact generation and artifact reuse
- Full safety-policy implementation
- Full experiment harness for memory contribution and report-ready result exports

### Post-First-Version Refinements

For the current rapid prototype, the backend core loop is considered good
enough: retrieval, generation, sentence-level memory extraction, persistence,
deduplication, and Hopfield recall are all implemented and covered by automated
tests. The remaining items below should therefore be treated as after-v1
refinement work rather than prerequisites for beginning the web UI:

- measurable `RAG-only` versus memory-enabled comparison exports
- memory-debug traces and report-oriented observability
- Russian-first real-chat threshold calibration and broader extraction tuning
- profile/artifact memory lifecycle behavior
- fine-grained positive memory type classification
- learned Hopfield projections or differentiable `ksoftmax`
- fuller safety and report-ready experiment harness work

### Immediate Next Steps

1. Finish the remaining `Web UI v1` slice, especially save/reload plan flow.
2. Tighten the UI's Russian-first copy and overall presentation polish.
3. Add minimal UI-facing safety and refusal presentation where the backend declines scope.
4. Keep the remaining backend memory-evaluation items as post-first-version refinement work.

### Current Risks and Notes

- The reranker question is no longer open for the current retrieval configuration. The tracked qrels show that reranking hurts ranking quality while adding substantial runtime cost, so it should stay off by default unless the corpus, qrels, or model stack changes materially.
- The current dense baseline is good enough to move forward. The measured retrieval elbow is locked at `top_k=10`, explicit citations are now working, and the baseline answer-eval export is no longer degenerate.
- Answer quality is baseline-acceptable, not polished. Some responses are still terse or stylistically rough, so future prompt work should be evidence-driven rather than assumed complete.
- The current local workflow now assumes repo-local model caching for both the generator and the retrieval query embedder. If those local artifacts are missing, the runtime may fall back to Hugging Face resolution and surprise the operator.
- The memory layer is materially more real now: it persists classifier-approved sentence-level user memory and performs a non-trainable Hopfield recall over real embedding vectors. What is still missing is the measured multi-arm comparison, Russian-first extraction quality, and the optional learned-projection phase.
- The repo now has standalone tooling plus a trained ru/en binary BiLSTM memory-extraction baseline, and the live backend now uses that tracked binary bundle in its sentence-level write path. The remaining quality gap is calibration and evaluation, not wiring.
- The preferred runtime splitter is now `pySBD`, but environments that have not yet been refreshed from `requirements.txt` will fall back to regex sentence splitting.
- The binary extractor metrics are encouraging on the tracked synthetic split, but the corpus still contains some noisy sentences. Synthetic held-out scores therefore overstate real-chat readiness.
- The current repo is still answer-first rather than artifact-first. That is acceptable for the baseline RAG milestone, but the planned structured outputs and artifact reuse remain open work.
- The current web UI is intentionally thin and direct-to-backend. That is the right tradeoff for the first prototype, but richer client-side state, plan persistence, and polish remain open.
- The latest `direct_answer` contract tightening and the dev-server reload-watch exclusions are implemented in code but should still be treated as pending smoke revalidation.
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
  - live write path=`/chat/answer` extracts and upserts sentence-level memory approved by the tracked binary BiLSTM bundle
  - runtime sentence splitter=`pySBD` preferred, regex fallback when `pysbd` is missing
  - dedupe rule=`normalized text per user`
  - prompt path=`persisted memory is summarized through a non-trainable Hopfield recall step`
  - current vector basis=`active real semantic embedding stack via the retrieval embedder`
  - active recall modes=`Hopfield top1 recall and Hopfield topk superposed recall`
  - current top-k implementation=`exact top-k masking plus renormalization, not differentiable ksoftmax`
- Frontend:
  - stack=`React + Vite + TypeScript`
  - current surfaces=`profile selection, chat, citations, memory-used display, plan generation, memory inspection`
  - backend integration=`direct HTTP calls to FastAPI endpoints`
  - default dev URL=`http://127.0.0.1:5173`
  - configurable backend base URL=`VITE_API_BASE_URL`
- Memory-extraction tooling:
  - tracked raw corpus=`tooling/memory_extraction/data/synthetic_memory_sentences_v4.jsonl`
  - corpus size=`2500` sentence-level examples
  - binary split sizes=`train 2000 / dev 250 / test 250`
  - best tracked binary eval=`accuracy 0.976`, `macro_f1 0.9619`
  - main weakness=`ru:NO_MEMORY recall 0.84` on the tracked synthetic test split
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
теперь уже первый реальный embedding-based Hopfield slice для memory,
подключенный к live answer-flow, а также первый реальный slice web UI,
подключенный к live-backend.

### Что уже сделано

- Билингвальная authoritative-документация репозитория уже создана.
- Каноническое отслеживание решений уже работает.
- Есть инструкции локальной настройки для WSL, Windows и macOS.
- Существует Python-first backend scaffold с FastAPI routing и явными service boundaries.
- Уже существует базовый нетренируемый Hopfield memory-read поверх реального semantic embedding stack с явными режимами `top1` и `topk`.
- Существует standalone tooling для preprocessing и перевода ESCO в `tooling/translation/`.
- Теперь также существует standalone tooling для synthetic-data и BiLSTM-training memory extraction в `tooling/memory_extraction/`.
- Synthetic-data generator теперь ротирует prompt variants, отбрасывает повторяющиеся openings и token-set near-duplicates и останавливает collapsed buckets по последовательным no-progress attempts вместо тихого зависания.
- Raw extraction-corpus сохраняет fine-grained labels, но первый supervised extractor baseline теперь бинарный: `MEMORY` против `NO_MEMORY`, а не сразу пяти-классовый multiclass.
- Standalone binary BiLSTM extraction-baseline теперь уже обучен, оценен и подключен к live backend write-path через sentence-level extraction.
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
- Live-flow `/chat/answer` теперь извлекает sentence-level memory-candidates через отслеживаемый binary BiLSTM bundle и сохраняет их до retrieval и prompt assembly.
- Runtime sentence-segmentation теперь предпочитает `pySBD` и откатывается к regex-splitting, если `pysbd` еще не установлен в app-env.
- Текущее правило дедупликации memory — уникальность normalized-text отдельно для каждого пользователя.
- Live prompt-path теперь суммирует persisted memory через базовый нетренируемый Hopfield recall-step поверх реальных embedding-векторов.
- Unit-тесты теперь покрывают текущие режимы Hopfield recall в `backend/tests/test_hopfield_memory.py`.
- Wrapper backend dev-server теперь собирает reload-glob как relative patterns, и это поведение покрыто `backend/tests/test_dev_server_scripts.py`.
- Теперь уже существует легкий web UI на React + Vite в каталоге `frontend/`.
- Первый UI-slice уже покрывает выбор профиля, grounded-chat, citations, отображение “memory used”, structured plan generation и memory inspection.
- Backend теперь явно разрешает стандартные local frontend dev-origins через CORS-конфигурацию.

### Текущая граница завершения

Следующая чистая граница проекта называется:

- `Memory Layer v1 Integrated`

Эту границу можно считать закрытой только тогда, когда одновременно выполнены все условия:

1. persistent-memory storage стабилен и inspectable через активный локальный app-flow
2. live answer-path записывает extracted memory до retrieval/prompt assembly
3. memory-read использует реальный embedding-based Hopfield-механизм с явными режимами `top1` и `topk`, а не placeholder hash-scaffold
4. существуют и отслеживаются outputs для `RAG-only`, `RAG + naive memory`, `RAG + Hopfield top1` и `RAG + Hopfield topk`
5. extraction памяти работает приемлемо для Russian-first usage, а не только через английские trigger-phrases
6. memory-enabled evaluation-output и документация репозитория отражают это состояние

Текущий статус относительно этой границы:

- `1` выполнен для текущего SQLite-backed scope
- `2` выполнен
- `3` выполнен
- `4` не выполнен
- `5` не выполнен
- `6` не выполнен

Результат по границе:

- `Memory Layer v1 Integrated` пока не закрыт.

### Что сейчас в работе

- Завершение оставшегося slice `Web UI v1`, прежде всего save/reload plan-flow и Russian-first polish.
- Реализация profile- и artifact-memory поверх текущего slice `memory_items`.
- Расширение evaluation harness от baseline RAG validation к сравнению naive-memory и Hopfield-memory поверх `RAG-only`.
- Измерение и калибровка live sentence-level extractor-а за пределами текущих synthetic-only evidence.
- Добавление memory-debug артефактов и comparison traces, чтобы текущий Hopfield-read был inspectable.
- Проверка предпочтительного runtime-path через `pySBD` в обновленных локальных app-env и измерение качества extraction на реальном чате.

### Что еще не сделано

- Редактируемое persistent storage для user profile и artifact memory
- Confirmation/archive/supersede flow для uncertain или устаревшей memory
- Более богатые extraction и consolidation памяти за пределами текущего normalized-text dedupe-rule
- Отслеживаемая evaluation `RAG-only` против naive-memory и Hopfield-memory
- Bilingual memory detection, которая приемлемо ведет себя на реальном чате, а не только на synthetic-data
- Измеренное bilingual memory detection, приемлемое на реальном чате, а не только на synthetic benchmark
- Более поздняя fine-grained type-classification для `PREFERENCE`, `CONSTRAINT`, `GOAL` и `AVAILABILITY`
- Memory-debug exports, comparison traces и report-ready артефакты
- Learned projections и differentiable `ksoftmax` как будущая фаза Hopfield-слоя
- Структурированная генерация career/wellbeing artifacts и их повторное использование
- Полноценная реализация safety policy
- Полноценный experiment harness для вклада memory и report-ready экспорт результатов

### Ближайшие шаги

1. Завершить оставшийся slice `Web UI v1`, прежде всего save/reload plan-flow.
2. Подтянуть Russian-first copy и общую presentation-polish UI.
3. Добавить минимальную UI-подачу safety/refusal, когда backend отклоняет запрос по scope.
4. Оставить оставшиеся backend memory-evaluation items как post-first-version refinement work.

### Текущие риски и заметки

- Вопрос о reranker для текущей retrieval-конфигурации больше не является открытым. Отслеживаемые qrels показывают, что reranking ухудшает ranking quality и одновременно добавляет заметную runtime-стоимость, поэтому по умолчанию он должен оставаться выключенным, если только корпус, qrels или model stack существенно не изменятся.
- Текущий dense baseline уже достаточно хорош, чтобы двигаться дальше. Retrieval-elbow зафиксирован на `top_k=10`, explicit citations работают, а baseline answer-eval export больше не является вырожденным.
- Качество ответов уже приемлемо для baseline, но еще не отполировано. Некоторые ответы все еще слишком краткие или стилистически грубые, поэтому будущая prompt-доработка должна быть опираться на evidence, а не на ощущения.
- Текущий локальный workflow теперь предполагает repo-local model caching и для generator, и для retrieval query-embedder. Если эти локальные артефакты отсутствуют, runtime может неожиданно обратиться к Hugging Face.
- Memory-layer теперь существенно более реален: он сохраняет classifier-approved sentence-level user memory и выполняет нетренируемый Hopfield recall поверх реальных embedding-векторов. Все еще не хватает измеряемого многорукавного comparison-report, качества Russian-first extraction и, при необходимости, learned-projection фазы.
- В репозитории теперь есть standalone tooling и уже обученный ru/en binary BiLSTM-baseline для memory extraction, и live-backend теперь уже использует этот tracked binary bundle в sentence-level write-path. Оставшийся разрыв — это калибровка и evaluation, а не wiring.
- Предпочтительный runtime-splitter теперь `pySBD`, но env-ы, которые еще не были обновлены из `requirements.txt`, будут откатываться к regex sentence-splitting.
- Метрики binary extractor выглядят обнадеживающе на отслеживаемом synthetic split, но corpus все еще содержит некоторый шум. Поэтому synthetic held-out scores завышают готовность к реальному чату.
- Текущий repo все еще answer-first, а не artifact-first. Для baseline RAG это допустимо, но planned structured outputs и artifact reuse все еще остаются открытой работой.
- Текущий web UI намеренно тонкий и direct-to-backend. Для первого prototype это правильный компромисс, но более богатое client-side state-management, plan persistence и polish все еще остаются открытой работой.
- Последние изменения с `direct_answer` contract и исключениями для reload-watch реализованы в коде, но их все еще нужно считать ожидающими smoke-подтверждения.
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
  - live write path=`/chat/answer` извлекает и upsert-ит sentence-level memory, одобренную отслеживаемым binary BiLSTM bundle
  - runtime sentence-splitter=`pySBD` preferred, regex fallback при отсутствии `pysbd`
  - dedupe rule=`normalized text per user`
  - prompt path=`persisted memory суммируется через нетренируемый Hopfield recall-step`
  - current vector basis=`активный real semantic embedding stack через retrieval-embedder`
  - active recall modes=`Hopfield top1 recall и Hopfield topk superposed recall`
  - current top-k implementation=`exact top-k masking plus renormalization, а не differentiable ksoftmax`
- Frontend:
  - stack=`React + Vite + TypeScript`
  - текущие поверхности=`выбор профиля, чат, citations, отображение memory-used, генерация плана, memory inspection`
  - backend integration=`прямые HTTP-запросы к FastAPI-endpoint`
  - default dev URL=`http://127.0.0.1:5173`
  - настраиваемый backend base URL=`VITE_API_BASE_URL`
- Memory-extraction tooling:
  - tracked raw corpus=`tooling/memory_extraction/data/synthetic_memory_sentences_v4.jsonl`
  - размер corpus=`2500` sentence-level примеров
  - размеры binary-split=`train 2000 / dev 250 / test 250`
  - лучшая отслеживаемая binary-eval=`accuracy 0.976`, `macro_f1 0.9619`
  - основная слабость=`ru:NO_MEMORY recall 0.84` на отслеживаемом synthetic test split
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
