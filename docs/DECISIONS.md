# Active Decisions

Last updated: 2026-03-23

Последнее обновление: 2026-03-23

## D-001 Product Direction

**English**

- Status: active
- Decision: The product is a web-based career-guidance and work-life balance assistant.
- Rationale: This aligns with the repository identity and the student’s academic objective. Mobile and Android planning is out of scope for the active repository direction.

**Русский**

- Статус: активно
- Решение: Продукт является веб-ориентированным ассистентом по карьерному сопровождению и work-life balance.
- Обоснование: Это соответствует идентичности репозитория и академической цели студентки. Mobile и Android planning находятся вне активных границ репозитория.

## D-002 Primary Languages

**English**

- Status: active
- Decision: Use Python for backend and AI/data pipeline work. Use JavaScript or TypeScript for frontend work.
- Rationale: The student already knows Python and JavaScript, so the project should remain maximally understandable and maintainable.

**Русский**

- Статус: активно
- Решение: Использовать Python для backend и AI/data pipeline. Использовать JavaScript или TypeScript для frontend.
- Обоснование: Студентка уже знает Python и JavaScript, поэтому проект должен оставаться максимально понятным и сопровождаемым.

## D-003 Generator Runtime

**English**

- Status: active
- Decision: The default generator path is `Qwen/Qwen3-0.6B` served through an OpenAI-compatible local GGUF server, with `llama-cpp-python[server]` as the preferred local implementation.
- Pinned artifact: `Qwen/Qwen3-0.6B-GGUF:Q8_0`
- Rationale: This keeps the generation model compact while moving to the stronger Qwen3 generation line, aligns the generator with the same Qwen3 model family used for retrieval, keeps the backend isolated behind a simple HTTP boundary, and avoids requiring a hand-built external `llama.cpp` binary in the normal setup flow.

**Русский**

- Статус: активно
- Решение: Путь генератора по умолчанию - `Qwen/Qwen3-0.6B`, обслуживаемый через локальный OpenAI-compatible GGUF-server, где `llama-cpp-python[server]` является предпочтительной локальной реализацией.
- Зафиксированный артефакт: `Qwen/Qwen3-0.6B-GGUF:Q8_0`
- Обоснование: Это сохраняет генератор компактным, одновременно переводя его на более сильную линейку Qwen3, выравнивает генератор с тем же семейством Qwen3, которое используется для retrieval, сохраняет простой HTTP-барьер между backend и runtime и избавляет обычный setup-flow от необходимости вручную собирать внешний бинарник `llama.cpp`.

## D-004 Retrieval Stack

**English**

- Status: active
- Decision: The retrieval stack uses SQLite to persist chunk text, provenance metadata, and embedding payloads, while dense ANN retrieval is handled by FAISS HNSW.
- Rationale: SQLite remains appropriate for local persistence and inspection, but the vector index itself should be a real ANN structure rather than a database pretending to be one.

**Русский**

- Статус: активно
- Решение: Retrieval stack использует SQLite для сохранения chunk text, provenance metadata и embedding payloads, а dense ANN-retrieval выполняется через FAISS HNSW.
- Обоснование: SQLite остается подходящим для локального хранения и инспекции, но сам vector index должен быть настоящей ANN-структурой, а не базой данных, притворяющейся таковой.

## D-005 User Language Priority

**English**

- Status: active
- Decision: The product is Russian-first for end users. English remains a supported language for collaboration, documentation, and review.
- Rationale: This matches the real audience and keeps implementation decisions aligned with the actual demo and thesis context.

**Русский**

- Статус: активно
- Решение: Продукт в первую очередь ориентирован на русскоязычных конечных пользователей. Английский язык остается поддерживаемым для совместной работы, документации и ревью.
- Обоснование: Это соответствует реальной аудитории проекта и не дает реализации отклониться от фактического demo- и thesis-контекста.

## D-006 Memory Novelty Framing

**English**

- Status: active
- Decision: The project's main personalization novelty is a real embedding-space Hopfield memory mechanism with explicit `top1` max-energy recall and `topk` superposed recall modes. The current repo state already includes a basic non-trainable implementation of that mechanism, but it must not be presented as if it already covers the optional learned-projection and differentiable-`ksoftmax` phase.
- Rationale: This connects the student's recurrent-network background, especially LSTM-focused study, to a defensible associative-memory contribution grounded in modern Hopfield literature. The actual claim is not "softmax over memory rows"; it is that the project evaluates explicit Hopfield-like recall regimes as the personalization mechanism over stored embedding vectors.
- Basis: Davydov, Jaffe, Singh, and Bullo, "Retrieving k-Nearest Memories with Modern Hopfield Networks", committed in the repo at `docs/papers/33_Retrieving_k_Nearest_Memori.pdf` and `docs/papers/hopfield_memory.txt`.
- Constraint: Documentation must distinguish clearly between the current non-trainable phase and any later learned-projection phase. The repo may call the current helper a basic Hopfield implementation, but it must not claim differentiable `ksoftmax` or learned memory projections that are not yet built.

**Русский**

- Статус: активно
- Решение: Главная personalization-новизна проекта — это реальный Hopfield-механизм памяти в embedding-space с явными режимами `top1` max-energy recall и `topk` superposed recall. Текущее состояние репозитория уже включает базовую нетренируемую реализацию этого механизма, но его нельзя представлять так, будто он уже покрывает optional learned-projection и differentiable-`ksoftmax` фазу.
- Обоснование: Это в защищаемой форме связывает бэкграунд студентки в recurrent networks, особенно обучение с акцентом на LSTM, с defensible associative-memory contribution, опирающимся на modern Hopfield literature. Реальное утверждение здесь не про «softmax по memory rows», а про оценку явных Hopfield-like recall regimes как механизма персонализации поверх сохраненных embedding-векторов.
- Основание: Davydov, Jaffe, Singh и Bullo, "Retrieving k-Nearest Memories with Modern Hopfield Networks"; работа зафиксирована в репозитории как `docs/papers/33_Retrieving_k_Nearest_Memori.pdf` и `docs/papers/hopfield_memory.txt`.
- Ограничение: Документация должна четко различать текущую нетренируемую фазу и возможную будущую learned-projection фазу. Репозиторий может называть текущий helper базовой реализацией Hopfield, но не должен утверждать наличие differentiable `ksoftmax` или learned memory projections, если они еще не построены.

## D-007 Evaluation Baseline

**English**

- Status: active
- Decision: The core memory experiment must compare `RAG-only`, `RAG + naive memory retrieval`, `RAG + Hopfield top1 recall`, and `RAG + Hopfield topk recall`.
- Rationale: This isolates whether the specific memory-retrieval policy adds measurable personalization value beyond baseline RAG and beyond a simpler memory lookup. It turns the novelty claim into an actual ablation rather than a naming exercise.

**Русский**

- Статус: активно
- Решение: Основной memory-эксперимент должен сравнивать `RAG-only`, `RAG + naive memory retrieval`, `RAG + Hopfield top1 recall` и `RAG + Hopfield topk recall`.
- Обоснование: Это позволяет изолировать, дает ли конкретная memory-retrieval policy измеримую personalization-ценность сверх baseline RAG и сверх более простого memory lookup. Так novelty-claim превращается в реальную ablation-схему, а не в упражнение по именованию.

## D-008 Documentation Policy

**English**

- Status: active
- Decision: Authoritative repository documentation must be bilingual in English and Russian.
- Rationale: The project should be understandable to both technical reviewers and the student across both languages without fragmenting the codebase itself.

**Русский**

- Статус: активно
- Решение: Авторитетная документация репозитория должна быть двуязычной: на английском и русском языках.
- Обоснование: Проект должен быть понятен как техническим проверяющим, так и студентке на обоих языках без раздробления самого кодового базиса.

## D-009 Bilingual Scenarios

**English**

- Status: active
- Decision: Evaluation scenarios and other enduring user-facing demo artifacts should include both English and Russian variants where practical.
- Rationale: The repository is bilingual by design, and the demo should show that the product concept can be exercised in both working languages.

**Русский**

- Статус: активно
- Решение: Evaluation-сценарии и другие долговечные user-facing demo-артефакты должны, где это практически возможно, включать варианты как на английском, так и на русском языках.
- Обоснование: Репозиторий изначально задуман как двуязычный, и демонстрация должна показывать, что концепция продукта может использоваться на обоих рабочих языках.

## D-010 Retrieval Models

**English**

- Status: active
- Decision: The retrieval stack uses `Qwen/Qwen3-Embedding-0.6B` as the active dense baseline. `Qwen/Qwen3-Reranker-0.6B` is retained only as a scored ablation artifact and is disabled by default in runtime configuration.
- Rationale: This keeps the retrieval stack multilingual and aligned with the current Qwen family. The tracked qrels now show that the reranker hurts ranking quality while adding significant runtime cost, so it has not earned a place in the active path.

**Русский**

- Статус: активно
- Решение: Retrieval stack использует `Qwen/Qwen3-Embedding-0.6B` как активный dense baseline. `Qwen/Qwen3-Reranker-0.6B` сохраняется только как scored ablation-артефакт и отключен по умолчанию в runtime-конфигурации.
- Обоснование: Это сохраняет multilingual retrieval stack и выравнивает проект по текущему семейству Qwen. Отслеживаемые qrels теперь показывают, что reranker ухудшает ranking quality и одновременно добавляет заметную runtime-стоимость, поэтому он не заслужил места в активном path.

## D-011 Progress Tracking

**English**

- Status: active
- Decision: Repository-native progress tracking should live in `docs/ROADMAP.md` and `docs/STATUS.md`.
- Rationale: This gives the project a durable, low-overhead planning and reporting mechanism without needing an external ticketing system.

**Русский**

- Статус: активно
- Решение: Внутреннее отслеживание прогресса проекта должно вестись в `docs/ROADMAP.md` и `docs/STATUS.md`.
- Обоснование: Это дает проекту устойчивый и малозатратный механизм планирования и отчетности без необходимости подключать внешнюю ticket-систему.

## D-012 ESCO Artifact Tracking

**English**

- Status: active
- Decision: Raw ESCO vendor downloads should remain ignored by git, while the normalized ESCO concept and relation JSONL artifacts, the bilingual translated ESCO concept corpus, and the preprocessing manifests should be tracked by git.
- Rationale: The raw vendor dump is reproducible from ESCO, but the normalized concept graph, normalized relation graph, bilingual translated corpus, and manifests together form the self-contained academic source layer needed to continue implementation without rerunning preprocessing.

**Русский**

- Статус: активно
- Решение: Raw ESCO vendor downloads должны оставаться игнорируемыми git, а нормализованные ESCO JSONL-артефакты concept и relation, двуязычный translated ESCO concept corpus и preprocessing manifests должны отслеживаться git.
- Обоснование: Raw vendor dump воспроизводим из ESCO, тогда как нормализованный graph concept и relation, двуязычный translated corpus и manifests вместе образуют самодостаточный академический source layer, необходимый для продолжения реализации без повторного запуска preprocessing.

## D-013 ESCO URI And Deduplication

**English**

- Status: active
- Decision: ESCO `conceptUri` values are the canonical concept identifiers used to join bilingual concept text to the ESCO relation graph, and duplicate source concept rows with the same URI should be collapsed during preprocessing by keeping the latest `modifiedDate`.
- Rationale: The URI is the stable graph key. The current ESCO English CSV dump contains a small number of duplicate concept rows that differ only by `modifiedDate`, so preprocessing should remove that vendor-data duplication rather than carrying it into tracked bilingual artifacts.

**Русский**

- Статус: активно
- Решение: Значения ESCO `conceptUri` являются каноническими идентификаторами concept, используемыми для связывания bilingual concept text с ESCO relation graph, а duplicate source concept rows с одинаковым URI должны схлопываться во время preprocessing с сохранением самой новой `modifiedDate`.
- Обоснование: URI является стабильным graph key. Текущий English CSV dump ESCO содержит небольшое число duplicate concept rows, которые отличаются только `modifiedDate`, поэтому preprocessing должен удалять это дублирование vendor data, а не переносить его в отслеживаемые bilingual artifacts.

## D-014 Dense Retrieval Backend

**English**

- Status: active
- Decision: The primary retrieval path should use FAISS HNSW for dense ANN search over the ESCO chunk corpus, while SQLite should persist chunk text, provenance metadata, and stored embedding payloads for that FAISS-backed system.
- Rationale: SQLite is appropriate for local persistence and inspection, but it should not pretend to be the vector index. FAISS HNSW gives the project a proper ANN retrieval layer without introducing heavier external infrastructure.

**Русский**

- Статус: активно
- Решение: Основной retrieval path должен использовать FAISS HNSW для dense ANN-search по корпусу ESCO chunk-ов, а SQLite должен сохранять chunk text, provenance metadata и embedding payloads для этой FAISS-backed системы.
- Обоснование: SQLite подходит для локального хранения и инспекции, но не должен притворяться vector index. FAISS HNSW дает проекту корректный ANN retrieval layer без введения более тяжелой внешней инфраструктуры.

## D-015 Retrieval Build Workflow

**English**

- Status: active
- Decision: Retrieval artifacts should be built explicitly with `python -m backend.scripts.build_retrieval_index` instead of being seeded lazily on the first user query. When the tracked FAISS cache is already current, the same command may restore stale SQLite retrieval rows without forcing a second full corpus-embedding pass.
- Rationale: The build step is reproducible but expensive enough to deserve an explicit operator command, especially once real Qwen3 embeddings are involved. This keeps runtime behavior predictable, makes retrieval-refresh work auditable, and allows cheap recovery of local SQLite state from the persisted FAISS cache.

**Русский**

- Статус: активно
- Решение: Retrieval-артефакты должны собираться явно через `python -m backend.scripts.build_retrieval_index`, а не лениво при первом пользовательском запросе. Если отслеживаемый FAISS-cache уже актуален, та же команда может восстановить устаревшие SQLite retrieval-rows без повторного полного прохода эмбеддинга по корпусу.
- Обоснование: Шаг сборки воспроизводим, но достаточно затратен, чтобы заслуживать явную операторскую команду, особенно после перехода на реальные Qwen3 embeddings. Это делает runtime-поведение предсказуемым, упрощает аудит workflow обновления retrieval и позволяет дешево восстанавливать локальное SQLite-состояние из persisted FAISS-cache.

## D-016 Tracked Retrieval Cache Artifacts

**English**

- Status: active
- Decision: The persisted FAISS retrieval artifacts `data/processed/retrieval/faiss_hnsw.index` and `data/processed/retrieval/faiss_hnsw_manifest.json` should be tracked by git for the active Qwen3 retrieval configuration. The local SQLite database remains untracked.
- Rationale: The FAISS HNSW build is expensive enough to justify caching in the repository, while the SQLite retrieval table can now be restored cheaply from tracked ESCO source artifacts plus the tracked FAISS cache without repeating the full embedding job.

**Русский**

- Статус: активно
- Решение: Persisted FAISS retrieval-артефакты `data/processed/retrieval/faiss_hnsw.index` и `data/processed/retrieval/faiss_hnsw_manifest.json` должны отслеживаться git для активной конфигурации retrieval на Qwen3. Локальная SQLite-база при этом остается неотслеживаемой.
- Обоснование: Сборка FAISS HNSW достаточно дорога, чтобы ее имело смысл кэшировать в репозитории, тогда как SQLite retrieval-table теперь может быть дешево восстановлена из отслеживаемых ESCO source-артефактов и отслеживаемого FAISS-cache без повторного полного embedding-job.

## D-017 Minimal RAG Baseline

**English**

- Status: active
- Decision: The minimal RAG baseline for this repo is dense retrieval plus grounded generation. Reranking is not part of the active baseline.
- Rationale: The original RAG setup is retrieval followed by generation. The tracked qrels for this repo now show that reranking does not improve final recall and degrades ranking quality, so it should remain outside the active baseline unless future evidence changes.

**Русский**

- Статус: активно
- Решение: Минимальный RAG baseline для этого репозитория — это dense retrieval плюс grounded generation. Reranking не входит в активный baseline.
- Обоснование: Исходная постановка RAG — это retrieval, а затем generation. Отслеживаемые qrels этого репозитория теперь показывают, что reranking не улучшает итоговый recall и ухудшает ranking quality, поэтому он должен оставаться вне активного baseline, если только будущие данные не покажут обратное.

## D-018 Canonical Evaluation Axes

**English**

- Status: active
- Decision: Retrieval quality should be evaluated with IR-style metrics over labeled relevant chunks, specifically `Recall@k`, `MRR@k`, and `nDCG@k`. Answer quality should be evaluated separately along context relevance, answer faithfulness, and answer relevance.
- Rationale: This separates retriever quality from generation quality, makes top-k and reranker on/off ablations measurable, and aligns the repo with established retrieval evaluation practice plus RAG-specific answer-quality dimensions.

**Русский**

- Статус: активно
- Решение: Качество retrieval должно оцениваться IR-метриками по размеченным relevant chunk-ам, а именно `Recall@k`, `MRR@k` и `nDCG@k`. Качество ответов должно оцениваться отдельно по dimensions: context relevance, answer faithfulness и answer relevance.
- Обоснование: Это разделяет качество retriever и качество generation, делает измеримыми ablation-эксперименты по top-k и режимам reranker on/off и выравнивает репозиторий с устоявшейся практикой evaluation retrieval и с RAG-specific dimensions качества ответов.

## D-019 Canonical Benchmark Baseline

**English**

- Status: active
- Decision: The canonical retrieval benchmark baseline is CPU-only HNSW search over already-built retrieval artifacts. Dense, reranker, and full-context benchmark modes are explicit opt-in measurements, and the benchmark command must not rebuild retrieval artifacts implicitly.
- Rationale: This separates ANN behavior from model latency, avoids hiding expensive rebuild work inside a benchmark command, and gives the repo a stable default benchmark that is cheap enough to repeat.

**Русский**

- Статус: активно
- Решение: Канонический baseline retrieval-benchmark — это CPU-only HNSW-search по уже собранным retrieval-артефактам. Режимы dense, reranker и full-context являются явными opt-in измерениями, а benchmark-команда не должна неявно пересобирать retrieval-артефакты.
- Обоснование: Это отделяет поведение ANN от model-latency, не скрывает дорогую пересборку внутри benchmark-команды и дает репозиторию стабильный baseline-benchmark, который достаточно дешев для повторяемого запуска.

## D-020 Canonical Eval Fixtures

**English**

- Status: active
- Decision: Canonical evaluation fixtures must live in tracked repo files. Retrieval judgments should live in `eval/retrieval_qrels.json`, and answer-level evidence cases should live in `eval/answer_eval_cases.json`.
- Rationale: Top-k choices, reranker on/off ablations, and grounded-answer claims cannot be defended from ad hoc conversation memory or console notes. The evaluation basis has to be durable, inspectable, and versioned.

**Русский**

- Статус: активно
- Решение: Канонические evaluation-fixtures должны храниться в отслеживаемых файлах репозитория. Retrieval-judgments должны храниться в `eval/retrieval_qrels.json`, а answer-level evidence cases — в `eval/answer_eval_cases.json`.
- Обоснование: Выбор top-k, ablation-эксперименты с режимами reranker on/off и утверждения о grounded-answer нельзя защищать на основе ad hoc памяти разговора или консольных заметок. Основа evaluation должна быть долговечной, inspectable и versioned.

## D-021 Canonical Persisted Retrieval-Eval Outputs

**English**

- Status: active
- Decision: The current scored retrieval-eval state should be persisted in tracked files under `eval/out/`, specifically dense and reranker prediction exports plus their corresponding score reports.
- Rationale: These outputs capture the scored state of the current persisted retrieval index and retrieval settings. They should be durable repo artifacts rather than ephemeral console output, and they now also document the current negative reranker outcome.

**Русский**

- Статус: активно
- Решение: Текущее scored-состояние retrieval-eval должно сохраняться в отслеживаемых файлах в `eval/out/`, а именно в dense и reranker prediction-export и соответствующих score-report.
- Обоснование: Эти output фиксируют scored-состояние текущего persisted retrieval-index и retrieval-settings. Они должны быть долговечными артефактами репозитория, а не эфемерным console-output, и теперь также документируют текущий отрицательный результат reranker.

## D-022 Current Reranker Outcome

**English**

- Status: active
- Decision: Keep the reranker disabled by default.
- Evidence: The tracked score reports show identical `recall@20` (`0.8611` vs `0.8611`) but worse dense-versus-rerank results for `recall@10` (`0.7963` vs `0.7222`), `ndcg@10` (`0.9304` vs `0.8814`), and `ndcg@20` (`0.9397` vs `0.9048`).
- Rationale: The reranker is more expensive and is currently worse on the tracked qrels, so it should not be part of the active runtime path.

**Русский**

- Статус: активно
- Решение: Оставить reranker отключенным по умолчанию.
- Доказательство: Отслеживаемые score-report показывают одинаковый `recall@20` (`0.8611` против `0.8611`), но худшие dense-versus-rerank результаты для `recall@10` (`0.7963` против `0.7222`), `ndcg@10` (`0.9304` против `0.8814`) и `ndcg@20` (`0.9397` против `0.9048`).
- Обоснование: Reranker дороже по runtime и в текущем виде хуже на отслеживаемых qrels, поэтому он не должен входить в активный runtime-path.

## D-023 Active Dense-Only Retrieval Default

**English**

- Status: active
- Decision: Lock the active dense-only runtime default at `top_k=10`.
- Evidence: The tracked dense-only tuning report shows the practical elbow at `top_k=10`, with `recall@10=0.7963` and `ndcg@10=0.9304`, while `top_k=20` only adds diminishing recall gains (`recall@20=0.8611`, `ndcg@20=0.9397`) at the cost of larger grounded context.
- Rationale: `top_k=10` captures most of the measured retrieval benefit without paying the full prompt-size cost of `top_k=20`, and is therefore the best current dense-only runtime tradeoff.

**Русский**

- Статус: активно
- Решение: Зафиксировать активный dense-only runtime-default на `top_k=10`.
- Доказательство: Отслеживаемый dense-only tuning-report показывает практический elbow на `top_k=10`, где `recall@10=0.7963` и `ndcg@10=0.9304`, тогда как `top_k=20` дает уже убывающую прибавку recall (`recall@20=0.8611`, `ndcg@20=0.9397`) ценой большего grounded-context.
- Обоснование: `top_k=10` захватывает большую часть измеренной retrieval-пользы без полной цены `top_k=20` по размеру prompt, поэтому на текущий момент это лучший dense-only runtime tradeoff.

## D-024 Candidate Pool In Active Dense-Only Mode

**English**

- Status: active
- Decision: Treat `candidate_pool` as inactive in the live dense-only runtime path while reranking remains disabled.
- Evidence: The tracked dense-only tuning output shows identical scores for all tested `candidate_pool` values at the same `top_k`, and the active path no longer reranks candidates.
- Rationale: Leaving `candidate_pool` in the active path would imply a runtime tuning lever that currently does not exist. It should remain only for explicit ablation or future reranker work.

**Русский**

- Статус: активно
- Решение: Считать `candidate_pool` неактивным в live dense-only runtime-path, пока reranking остается выключенным.
- Доказательство: Отслеживаемый dense-only tuning-output показывает одинаковые score для всех протестированных значений `candidate_pool` при одном и том же `top_k`, а активный path больше не делает reranking candidates.
- Обоснование: Оставлять `candidate_pool` в активном path означало бы притворяться, что сейчас существует runtime-рычаг настройки, которого на деле нет. Он должен сохраняться только для явных ablation-экспериментов или будущей работы с reranker.

## D-025 Local Runtime Artifact Policy

**English**

- Status: active
- Decision: Local generator and retrieval-runtime model artifacts must be cached under repo-local ignored paths in `models/`, and helper scripts must generate `.env.local` plus the local generation-server config automatically.
- Rationale: The project now depends on local model artifacts for repeatable generation and query-embedding behavior, but those artifacts are too large and machine-specific for Git. Keeping them repo-local, ignored, and script-managed makes the workflow reproducible without pretending the artifacts are source-controlled.

**Русский**

- Статус: активно
- Решение: Локальные model-артефакты для generator и retrieval-runtime должны кэшироваться в игнорируемых repo-local путях внутри `models/`, а helper-скрипты должны автоматически генерировать `.env.local` и локальную конфигурацию generation-server.
- Обоснование: Теперь проект зависит от локальных model-артефактов для повторяемого поведения generation и query-embedding, но эти артефакты слишком велики и слишком machine-specific для Git. Хранение их в repo-local ignored-path и управление через скрипты делает workflow воспроизводимым, не притворяясь, что эти артефакты контролируются Git.

## D-026 Answer-Evidence Citation Attribution

**English**

- Status: active
- Decision: Canonical answer-evidence scoring must rely on explicit model-selected `cited_chunk_ids`. The system must not score the entire retrieved context as if every retrieved chunk had been cited.
- Rationale: Treating the whole retrieval context as citations makes answer-evidence precision collapse as `top_k` grows and turns the metric into a proxy for context width rather than attribution quality. The canonical answer export must therefore preserve explicit citation selection.

**Русский**

- Статус: активно
- Решение: Канонический score для answer-evidence должен опираться на явные `cited_chunk_ids`, выбранные моделью. Система не должна score-ить весь retrieved-context так, как будто каждая извлеченная запись была процитирована.
- Обоснование: Если считать цитатами весь retrieval-context, precision для answer-evidence разрушается по мере роста `top_k`, и метрика превращается в прокси ширины context, а не качества атрибуции. Поэтому канонический export ответов обязан сохранять явный выбор citation-ID.

## D-027 Persistent Memory Store And Write Path

**English**

- Status: active
- Decision: The active memory store should be SQLite-backed through the `memory_items` table, and the live `/chat/answer` path should extract sentence-level memory candidates before retrieval/prompt assembly.
- Rationale: The project is past the point where an in-process dictionary is a defensible personalization layer. Persisting memory through SQLite gives the repo an inspectable, durable state boundary, and wiring extraction into the live answer path creates the minimum viable basis for later `RAG-only` versus `RAG + memory` evaluation.

**Русский**

- Статус: активно
- Решение: Активный memory-store должен быть SQLite-backed через таблицу `memory_items`, а live-path `/chat/answer` должен извлекать sentence-level memory-candidates до retrieval/prompt assembly.
- Обоснование: Проект уже вышел за пределы точки, где in-process dictionary можно считать защищаемым personalization-layer. Сохранение памяти через SQLite дает репозиторию inspectable и долговечную границу состояния, а подключение extraction в live answer-path создает минимально жизнеспособную основу для последующего сравнения `RAG-only` и `RAG + memory`.

## D-028 Memory Vector Basis

**English**

- Status: active
- Decision: The active memory read/write vector basis must use the real semantic embedding stack, not the deterministic hash placeholder.
- Rationale: Hopfield-style recall in this project is performed over stored text embeddings. The current implementation therefore reuses the active retrieval embedder for query and memory vectors. A hash-based vector path is acceptable only as a temporary test scaffold and is not strong enough to support the scientific claim that the Hopfield layer adds meaningful personalization value.

**Русский**

- Статус: активно
- Решение: Активный vector-basis для memory read/write должен использовать реальный semantic embedding stack, а не deterministic hash placeholder.
- Обоснование: Hopfield-style recall в этом проекте выполняется поверх сохраненных text-embeddings. Поэтому текущая реализация повторно использует active retrieval-embedder для query- и memory-векторов. Hash-based vector-path допустим только как временный test-scaffold и недостаточно силен, чтобы поддерживать научное утверждение о meaningful personalization value от Hopfield-layer.

## D-029 Russian-First Memory Behavior

**English**

- Status: active
- Decision: Russian-first behavior applies to the memory layer as well as retrieval and generation. Memory extraction and consolidation should not remain English-triggered in the active end-state.
- Rationale: A bilingual retrieval layer plus an English-biased memory layer would create a misleading product behavior gap. The app must not appear multilingual in evidence retrieval while silently underperforming on personalization for Russian users.

**Русский**

- Статус: активно
- Решение: Russian-first behavior относится и к memory-layer, а не только к retrieval и generation. Memory extraction и consolidation не должны оставаться English-triggered в активном end-state.
- Обоснование: Bilingual retrieval-layer в сочетании с English-biased memory-layer создал бы вводящий в заблуждение product-behavior gap. Приложение не должно выглядеть multilingual в evidence retrieval и при этом молча уступать в personalization для русскоязычных пользователей.

## D-030 Structured Artifact End-State

**English**

- Status: active
- Decision: Grounded answering is the closed baseline, but it is not the full structured-generation end-state. Persisted structured artifacts such as career plans, skills-gap outputs, and wellbeing-oriented plans remain required deliverables.
- Rationale: The project plan and academic framing both assume more than a question-answering assistant. The repo should not let the current answer-first baseline masquerade as the completed structured-output scope.

**Русский**

- Статус: активно
- Решение: Grounded answering — это закрытый baseline, но не полный structured-generation end-state. Persisted structured artifacts, такие как career plans, skills-gap outputs и wellbeing-oriented plans, по-прежнему остаются обязательными deliverables.
- Обоснование: И project plan, и academic framing предполагают больше, чем просто вопросно-ответный ассистент. Репозиторий не должен позволять текущему answer-first baseline притворяться завершенным structured-output scope.

## D-031 Current Hopfield Implementation Phase

**English**

- Status: active
- Decision: The current shipped Hopfield phase is a basic non-trainable implementation over stored embedding vectors. `top1` recall is implemented as sharp single-memory selection, and `topk` recall is implemented as exact top-k masking plus renormalization over softmax weights.
- Rationale: This is the simplest academically defensible implementation that still matches the modern Hopfield retrieval story in the committed paper. It keeps the mechanism explicit and inspectable before any optional learned-projection or differentiable `ksoftmax` phase.
- Basis: The committed paper defines the one-step modern Hopfield update `x+ = Ξ softmax(βΞᵀ x)` and the k-Hopfield layer `X = Ξ ksoftmax(βΞᵀ x0)`. See `docs/papers/33_Retrieving_k_Nearest_Memori.pdf` and `docs/papers/hopfield_memory.txt`.

**Русский**

- Статус: активно
- Решение: Текущая поставляемая Hopfield-фаза — это базовая нетренируемая реализация поверх сохраненных embedding-векторов. Recall `top1` реализован как резкий выбор одной лучшей memory, а `topk` реализован как exact top-k masking с последующей перенормировкой softmax-весов.
- Обоснование: Это самое простое академически защищаемое решение, которое все еще соответствует modern Hopfield retrieval-story из зафиксированной в репозитории статьи. Оно сохраняет механизм явным и inspectable до любой optional learned-projection или differentiable `ksoftmax` фазы.
- Основание: В зафиксированной статье one-step modern Hopfield update задается как `x+ = Ξ softmax(βΞᵀ x)`, а k-Hopfield layer — как `X = Ξ ksoftmax(βΞᵀ x0)`. См. `docs/papers/33_Retrieving_k_Nearest_Memori.pdf` и `docs/papers/hopfield_memory.txt`.

## D-032 Memory Extraction Classifier Baseline

**English**

- Status: active
- Decision: The next memory-extraction baseline is a lightweight bilingual sentence classifier implemented as a BiLSTM, trained separately under `tooling/memory_extraction/`.
- Rationale: This keeps extraction small, inspectable, and academically aligned with the student's recurrent-network background. It also keeps extraction logically separate from Hopfield recall: the classifier decides whether a sentence should become memory, while later type classification and Hopfield recall remain separate concerns.
- Implementation note: Synthetic corpus generation for this classifier should run as direct standalone GPU tooling with explicit local model control, not through the app's OpenAI-compatible runtime server.
- Implementation note: The first supervised task is now binary `MEMORY` versus `NO_MEMORY`. Fine-grained labels remain in the raw synthetic corpus for later type-classification work, but the first BiLSTM baseline should not be forced to solve full type assignment on day one.
- Artifact note: The resulting synthetic corpora, split manifests, trained model bundles, and evaluation reports may be persisted in git when reproducibility of the extraction baseline matters.
- Constraint: The live backend may keep using heuristic extraction until the BiLSTM classifier is trained, evaluated, and integrated. Tooling can ship before runtime integration.

**Русский**

- Статус: активно
- Решение: Следующий baseline для memory extraction — это легкий двуязычный sentence-classifier на базе BiLSTM, обучаемый отдельно в `tooling/memory_extraction/`.
- Обоснование: Это сохраняет extraction небольшим, inspectable и академически согласованным с бэкграундом студентки в recurrent networks. Также это сохраняет логическое разделение extraction и Hopfield recall: классификатор решает, должна ли фраза стать memory, а более поздняя type-classification и Hopfield recall остаются отдельными задачами.
- Замечание по реализации: Генерация synthetic corpus для этого classifier должна выполняться как direct standalone GPU tooling с явным локальным контролем модели, а не через OpenAI-compatible runtime-server приложения.
- Замечание по реализации: Первая supervised-задача теперь бинарная: `MEMORY` против `NO_MEMORY`. Fine-grained labels сохраняются в raw synthetic corpus для более поздней type-classification фазы, но первый BiLSTM-baseline не должен сразу решать полную типизацию.
- Замечание по артефактам: Получающиеся synthetic corpora, split manifests, trained model bundles и evaluation reports могут сохраняться в git, когда важна воспроизводимость extraction-baseline.
- Ограничение: Live-backend может пока продолжать использовать heuristic extraction, пока BiLSTM-classifier не будет обучен, оценен и интегрирован. Tooling может поставляться раньше runtime-integration.

## D-033 Memory Extraction Label Schema

**English**

- Status: active
- Decision: The v1 sentence label schema for memory extraction is fixed to `NO_MEMORY`, `PREFERENCE`, `CONSTRAINT`, `GOAL`, and `AVAILABILITY`.
- Rationale: This gives the repo a small, defensible raw label space that is directly useful for personalization and later memory lifecycle work. `NO_MEMORY` provides the negative class, while the four positive labels map cleanly to later memory category and downstream policy.
- Constraint: The raw label schema does not imply that the first trained classifier must be five-way multiclass. The repo now uses those labels as raw supervision while deriving a first binary `MEMORY` vs `NO_MEMORY` task for the initial BiLSTM baseline.
- Constraint: v1 synthetic corpus generation targets only `ru` and `en`. Mixed-language handling is deferred until the bilingual baseline is trained and measured.

**Русский**

- Статус: активно
- Решение: Sentence label schema v1 для memory extraction фиксируется как `NO_MEMORY`, `PREFERENCE`, `CONSTRAINT`, `GOAL` и `AVAILABILITY`.
- Обоснование: Это дает репозиторию небольшой и защищаемый raw-набор меток, напрямую полезный для personalization и последующей memory-lifecycle логики. `NO_MEMORY` дает negative-class, а четыре positive-label cleanly отображаются на более поздние memory category и downstream policy.
- Ограничение: Raw label schema не означает, что первый обучаемый classifier обязан быть пяти-классовым multiclass. Репозиторий теперь использует эти метки как raw supervision, но выводит из них первую бинарную задачу `MEMORY` vs `NO_MEMORY` для начального BiLSTM-baseline.
- Ограничение: Synthetic corpus generation в v1 нацелено только на `ru` и `en`. Mixed-language handling откладывается до тех пор, пока bilingual baseline не будет обучен и измерен.

## D-034 Runtime Sentence Segmentation and Binary Memory Write Integration

**English**

- Status: active
- Decision: The first runtime integration of the trained BiLSTM extractor should operate on deterministic sentence-like segments, not on whole user turns and not through another LLM extraction pass.
- Decision: One incoming user message should be normalized, split into short sentence-like segments with `pySBD` when available and a newline-aware regex fallback otherwise, and each segment should be classified independently as `MEMORY` or `NO_MEMORY`.
- Decision: Accepted segments should be converted into one `MemoryItemPayload` each, deduplicated first within the request via `consolidate_memory_items(...)`, then persisted through `SqliteMemoryStore.upsert_item(...)`, which remains the canonical normalized-text-per-user dedupe layer.
- Decision: In the binary-only phase, accepted classifier outputs should use a coarse runtime category such as `user_memory`, store classifier probability as `confidence`, and keep a stable default `importance` until a separate type-classification phase exists.
- Decision: The Hopfield layer should not implement a second bespoke dedupe path. It should keep reading the already persisted and normalized `memory_items` set and perform recall over that list.
- Rationale: The classifier is sentence-level by design, so whole-turn classification would mix unrelated facts and questions into one decision. `pySBD` gives the runtime a lightweight deterministic bilingual sentence splitter without another model call, while the regex fallback keeps local app environments usable until dependencies are refreshed. Reusing the existing store-level dedupe keeps one canonical persistence policy instead of fragmenting memory-write logic across multiple modules.

**Русский**

- Статус: активно
- Решение: Первая runtime-интеграция обученного BiLSTM-extractor должна работать на детерминированных sentence-like segments, а не на whole user turn и не через еще один LLM extraction-pass.
- Решение: Одно входное сообщение пользователя должно нормализоваться, разбиваться на короткие sentence-like segments через `pySBD`, когда он доступен, и через newline-aware regex-fallback в противном случае, и каждый segment должен независимо классифицироваться как `MEMORY` или `NO_MEMORY`.
- Решение: Принятые segments должны превращаться в отдельные `MemoryItemPayload`, сначала дедуплицироваться внутри запроса через `consolidate_memory_items(...)`, а затем сохраняться через `SqliteMemoryStore.upsert_item(...)`, который остается каноническим normalized-text-per-user слоем дедупликации.
- Решение: В binary-only фазе принятые classifier outputs должны использовать coarse runtime-category вроде `user_memory`, сохранять вероятность classifier как `confidence` и держать стабильный default `importance`, пока не появится отдельная phase type-classification.
- Решение: Hopfield-layer не должен реализовывать второй отдельный dedupe-path. Он должен по-прежнему читать уже сохраненный и нормализованный набор `memory_items` и выполнять recall поверх этого списка.
- Обоснование: Classifier по своей природе sentence-level, поэтому whole-turn classification смешивала бы в одно решение несвязанные факты, вопросы и chat-fragments. `pySBD` дает runtime легкий детерминированный bilingual sentence-splitter без еще одного model-call, а regex-fallback сохраняет работоспособность локального app-env, пока зависимости не обновлены. Повторное использование store-level dedupe сохраняет одну каноническую policy persistence вместо того, чтобы дробить логику memory-write по разным модулям.

## Decision Maintenance Rule

**English**

When an active architectural, scope, stack, or evaluation decision changes, update this file in the same change.

**Русский**

Когда меняется активное архитектурное, scope-, stack- или evaluation-решение, обновляйте этот файл в том же изменении.
