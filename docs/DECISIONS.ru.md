# Active Decisions

Последнее обновление: 2026-03-24

## D-001 Product Direction

**Русский**

- Статус: активно
- Решение: Продукт является веб-ориентированным ассистентом по карьерному сопровождению и work-life balance.
- Обоснование: Это соответствует идентичности репозитория и академической цели студентки. Mobile и Android planning находятся вне активных границ репозитория.

## D-002 Primary Languages

**Русский**

- Статус: активно
- Решение: Использовать Python для backend и AI/data pipeline. Использовать JavaScript или TypeScript для frontend.
- Обоснование: Студентка уже знает Python и JavaScript, поэтому проект должен оставаться максимально понятным и сопровождаемым.

## D-003 Generator Runtime

**Русский**

- Статус: активно
- Решение: Путь генератора по умолчанию - `Qwen/Qwen3-0.6B`, обслуживаемый через локальный OpenAI-compatible GGUF-server, где `llama-cpp-python[server]` является предпочтительной локальной реализацией.
- Зафиксированный артефакт: `Qwen/Qwen3-0.6B-GGUF:Q8_0`
- Обоснование: Это сохраняет генератор компактным, одновременно переводя его на более сильную линейку Qwen3, выравнивает генератор с тем же семейством Qwen3, которое используется для retrieval, сохраняет простой HTTP-барьер между backend и runtime и избавляет обычный setup-flow от необходимости вручную собирать внешний бинарник `llama.cpp`.

## D-004 Retrieval Stack

**Русский**

- Статус: активно
- Решение: Retrieval stack использует SQLite для сохранения chunk text, provenance metadata и embedding payloads, а dense ANN-retrieval выполняется через FAISS HNSW.
- Обоснование: SQLite остается подходящим для локального хранения и инспекции, но сам vector index должен быть настоящей ANN-структурой, а не базой данных, притворяющейся таковой.

## D-005 User Language Priority

**Русский**

- Статус: активно
- Решение: Продукт в первую очередь ориентирован на русскоязычных конечных пользователей. Английский язык остается поддерживаемым для совместной работы, документации и ревью.
- Обоснование: Это соответствует реальной аудитории проекта и не дает реализации отклониться от фактического demo- и thesis-контекста.

## D-006 Memory Novelty Framing

**Русский**

- Статус: активно
- Решение: Главная personalization-новизна проекта — это реальный Hopfield-механизм памяти в embedding-space с явными режимами `top1` max-energy recall и `topk` superposed recall. Текущее состояние репозитория уже включает базовую нетренируемую реализацию этого механизма, но его нельзя представлять так, будто он уже покрывает optional learned-projection и differentiable-`ksoftmax` фазу.
- Обоснование: Это в защищаемой форме связывает бэкграунд студентки в recurrent networks, особенно обучение с акцентом на LSTM, с defensible associative-memory contribution, опирающимся на modern Hopfield literature. Реальное утверждение здесь не про «softmax по memory rows», а про оценку явных Hopfield-like recall regimes как механизма персонализации поверх сохраненных embedding-векторов.
- Основание: Davydov, Jaffe, Singh и Bullo, "Retrieving k-Nearest Memories with Modern Hopfield Networks"; работа зафиксирована в репозитории как `docs/papers/33_Retrieving_k_Nearest_Memori.pdf` и `docs/papers/hopfield_memory.txt`.
- Ограничение: Документация должна четко различать текущую нетренируемую фазу и возможную будущую learned-projection фазу. Репозиторий может называть текущий helper базовой реализацией Hopfield, но не должен утверждать наличие differentiable `ksoftmax` или learned memory projections, если они еще не построены.

## D-007 Evaluation Baseline

**Русский**

- Статус: активно
- Решение: Основной memory-эксперимент должен сравнивать `RAG-only`, `RAG + naive memory retrieval`, `RAG + Hopfield top1 recall` и `RAG + Hopfield topk recall`.
- Обоснование: Это позволяет изолировать, дает ли конкретная memory-retrieval policy измеримую personalization-ценность сверх baseline RAG и сверх более простого memory lookup. Так novelty-claim превращается в реальную ablation-схему, а не в упражнение по именованию.

## D-008 Documentation Policy

**Русский**

- Статус: активно
- Решение: Авторитетная документация репозитория должна существовать как на английском, так и на русском языке.
- Решение: Там, где это практически удобно, долговечные документы теперь следует вести в виде парных language-specific файлов вроде `*.en.md` и `*.ru.md`.
- Решение: Путь без языкового суффикса может оставаться compatibility-entrypoint или language-selector, если это помогает сохранить стабильные ссылки.
- Обоснование: Проект должен оставаться понятным и техническим проверяющим, и студентке, одновременно уменьшая стоимость сопровождения и проблемы читаемости очень больших mixed-language файлов.

## D-009 Bilingual Scenarios

**Русский**

- Статус: активно
- Решение: Evaluation-сценарии и другие долговечные user-facing demo-артефакты должны, где это практически возможно, включать варианты как на английском, так и на русском языках.
- Обоснование: Репозиторий изначально задуман как двуязычный, и демонстрация должна показывать, что концепция продукта может использоваться на обоих рабочих языках.

## D-010 Retrieval Models

**Русский**

- Статус: активно
- Решение: Retrieval stack использует `Qwen/Qwen3-Embedding-0.6B` как активный dense baseline. `Qwen/Qwen3-Reranker-0.6B` сохраняется только как scored ablation-артефакт и отключен по умолчанию в runtime-конфигурации.
- Обоснование: Это сохраняет multilingual retrieval stack и выравнивает проект по текущему семейству Qwen. Отслеживаемые qrels теперь показывают, что reranker ухудшает ranking quality и одновременно добавляет заметную runtime-стоимость, поэтому он не заслужил места в активном path.

## D-011 Progress Tracking

**Русский**

- Статус: активно
- Решение: Внутреннее отслеживание прогресса проекта должно вестись в `docs/ROADMAP.md` и `docs/STATUS.md`.
- Обоснование: Это дает проекту устойчивый и малозатратный механизм планирования и отчетности без необходимости подключать внешнюю ticket-систему.

## D-012 ESCO Artifact Tracking

**Русский**

- Статус: активно
- Решение: Raw ESCO vendor downloads должны оставаться игнорируемыми git, а нормализованные ESCO JSONL-артефакты concept и relation, двуязычный translated ESCO concept corpus и preprocessing manifests должны отслеживаться git.
- Обоснование: Raw vendor dump воспроизводим из ESCO, тогда как нормализованный graph concept и relation, двуязычный translated corpus и manifests вместе образуют самодостаточный академический source layer, необходимый для продолжения реализации без повторного запуска preprocessing.

## D-013 ESCO URI And Deduplication

**Русский**

- Статус: активно
- Решение: Значения ESCO `conceptUri` являются каноническими идентификаторами concept, используемыми для связывания bilingual concept text с ESCO relation graph, а duplicate source concept rows с одинаковым URI должны схлопываться во время preprocessing с сохранением самой новой `modifiedDate`.
- Обоснование: URI является стабильным graph key. Текущий English CSV dump ESCO содержит небольшое число duplicate concept rows, которые отличаются только `modifiedDate`, поэтому preprocessing должен удалять это дублирование vendor data, а не переносить его в отслеживаемые bilingual artifacts.

## D-014 Dense Retrieval Backend

**Русский**

- Статус: активно
- Решение: Основной retrieval path должен использовать FAISS HNSW для dense ANN-search по корпусу ESCO chunk-ов, а SQLite должен сохранять chunk text, provenance metadata и embedding payloads для этой FAISS-backed системы.
- Обоснование: SQLite подходит для локального хранения и инспекции, но не должен притворяться vector index. FAISS HNSW дает проекту корректный ANN retrieval layer без введения более тяжелой внешней инфраструктуры.

## D-015 Retrieval Build Workflow

**Русский**

- Статус: активно
- Решение: Retrieval-артефакты должны собираться явно через `python -m backend.scripts.build_retrieval_index`, а не лениво при первом пользовательском запросе. Если отслеживаемый FAISS-cache уже актуален, та же команда может восстановить устаревшие SQLite retrieval-rows без повторного полного прохода эмбеддинга по корпусу.
- Обоснование: Шаг сборки воспроизводим, но достаточно затратен, чтобы заслуживать явную операторскую команду, особенно после перехода на реальные Qwen3 embeddings. Это делает runtime-поведение предсказуемым, упрощает аудит workflow обновления retrieval и позволяет дешево восстанавливать локальное SQLite-состояние из persisted FAISS-cache.

## D-016 Tracked Retrieval Cache Artifacts

**Русский**

- Статус: активно
- Решение: Persisted FAISS retrieval-артефакты `data/processed/retrieval/faiss_hnsw.index` и `data/processed/retrieval/faiss_hnsw_manifest.json` должны отслеживаться git для активной конфигурации retrieval на Qwen3. Локальная SQLite-база при этом остается неотслеживаемой.
- Обоснование: Сборка FAISS HNSW достаточно дорога, чтобы ее имело смысл кэшировать в репозитории, тогда как SQLite retrieval-table теперь может быть дешево восстановлена из отслеживаемых ESCO source-артефактов и отслеживаемого FAISS-cache без повторного полного embedding-job.

## D-017 Minimal RAG Baseline

**Русский**

- Статус: активно
- Решение: Минимальный RAG baseline для этого репозитория — это dense retrieval плюс grounded generation. Reranking не входит в активный baseline.
- Обоснование: Исходная постановка RAG — это retrieval, а затем generation. Отслеживаемые qrels этого репозитория теперь показывают, что reranking не улучшает итоговый recall и ухудшает ranking quality, поэтому он должен оставаться вне активного baseline, если только будущие данные не покажут обратное.

## D-018 Canonical Evaluation Axes

**Русский**

- Статус: активно
- Решение: Качество retrieval должно оцениваться IR-метриками по размеченным relevant chunk-ам, а именно `Recall@k`, `MRR@k` и `nDCG@k`. Качество ответов должно оцениваться отдельно по dimensions: context relevance, answer faithfulness и answer relevance.
- Обоснование: Это разделяет качество retriever и качество generation, делает измеримыми ablation-эксперименты по top-k и режимам reranker on/off и выравнивает репозиторий с устоявшейся практикой evaluation retrieval и с RAG-specific dimensions качества ответов.

## D-019 Canonical Benchmark Baseline

**Русский**

- Статус: активно
- Решение: Канонический baseline retrieval-benchmark — это CPU-only HNSW-search по уже собранным retrieval-артефактам. Режимы dense, reranker и full-context являются явными opt-in измерениями, а benchmark-команда не должна неявно пересобирать retrieval-артефакты.
- Обоснование: Это отделяет поведение ANN от model-latency, не скрывает дорогую пересборку внутри benchmark-команды и дает репозиторию стабильный baseline-benchmark, который достаточно дешев для повторяемого запуска.

## D-020 Canonical Eval Fixtures

**Русский**

- Статус: активно
- Решение: Канонические evaluation-fixtures должны храниться в отслеживаемых файлах репозитория. Retrieval-judgments должны храниться в `eval/retrieval_qrels.json`, а answer-level evidence cases — в `eval/answer_eval_cases.json`.
- Обоснование: Выбор top-k, ablation-эксперименты с режимами reranker on/off и утверждения о grounded-answer нельзя защищать на основе ad hoc памяти разговора или консольных заметок. Основа evaluation должна быть долговечной, inspectable и versioned.

## D-021 Canonical Persisted Retrieval-Eval Outputs

**Русский**

- Статус: активно
- Решение: Текущее scored-состояние retrieval-eval должно сохраняться в отслеживаемых файлах в `eval/out/`, а именно в dense и reranker prediction-export и соответствующих score-report.
- Обоснование: Эти output фиксируют scored-состояние текущего persisted retrieval-index и retrieval-settings. Они должны быть долговечными артефактами репозитория, а не эфемерным console-output, и теперь также документируют текущий отрицательный результат reranker.

## D-022 Current Reranker Outcome

**Русский**

- Статус: активно
- Решение: Оставить reranker отключенным по умолчанию.
- Доказательство: Отслеживаемые score-report показывают одинаковый `recall@20` (`0.8611` против `0.8611`), но худшие dense-versus-rerank результаты для `recall@10` (`0.7963` против `0.7222`), `ndcg@10` (`0.9304` против `0.8814`) и `ndcg@20` (`0.9397` против `0.9048`).
- Обоснование: Reranker дороже по runtime и в текущем виде хуже на отслеживаемых qrels, поэтому он не должен входить в активный runtime-path.

## D-023 Active Dense-Only Retrieval Default

**Русский**

- Статус: активно
- Решение: Зафиксировать активный dense-only runtime-default на `top_k=10`.
- Доказательство: Отслеживаемый dense-only tuning-report показывает практический elbow на `top_k=10`, где `recall@10=0.7963` и `ndcg@10=0.9304`, тогда как `top_k=20` дает уже убывающую прибавку recall (`recall@20=0.8611`, `ndcg@20=0.9397`) ценой большего grounded-context.
- Обоснование: `top_k=10` захватывает большую часть измеренной retrieval-пользы без полной цены `top_k=20` по размеру prompt, поэтому на текущий момент это лучший dense-only runtime tradeoff.

## D-024 Candidate Pool In Active Dense-Only Mode

**Русский**

- Статус: активно
- Решение: Считать `candidate_pool` неактивным в live dense-only runtime-path, пока reranking остается выключенным.
- Доказательство: Отслеживаемый dense-only tuning-output показывает одинаковые score для всех протестированных значений `candidate_pool` при одном и том же `top_k`, а активный path больше не делает reranking candidates.
- Обоснование: Оставлять `candidate_pool` в активном path означало бы притворяться, что сейчас существует runtime-рычаг настройки, которого на деле нет. Он должен сохраняться только для явных ablation-экспериментов или будущей работы с reranker.

## D-025 Local Runtime Artifact Policy

**Русский**

- Статус: активно
- Решение: Локальные model-артефакты для generator и retrieval-runtime должны кэшироваться в игнорируемых repo-local путях внутри `models/`, а helper-скрипты должны автоматически генерировать `.env.local` и локальную конфигурацию generation-server.
- Обоснование: Теперь проект зависит от локальных model-артефактов для повторяемого поведения generation и query-embedding, но эти артефакты слишком велики и слишком machine-specific для Git. Хранение их в repo-local ignored-path и управление через скрипты делает workflow воспроизводимым, не притворяясь, что эти артефакты контролируются Git.

## D-026 Answer-Evidence Citation Attribution

**Русский**

- Статус: активно
- Решение: Канонический score для answer-evidence должен опираться на явные `cited_chunk_ids`, выбранные моделью. Система не должна score-ить весь retrieved-context так, как будто каждая извлеченная запись была процитирована.
- Обоснование: Если считать цитатами весь retrieval-context, precision для answer-evidence разрушается по мере роста `top_k`, и метрика превращается в прокси ширины context, а не качества атрибуции. Поэтому канонический export ответов обязан сохранять явный выбор citation-ID.

## D-027 Persistent Memory Store And Write Path

**Русский**

- Статус: активно
- Решение: Активный memory-store должен быть SQLite-backed через таблицу `memory_items`, а live-path `/chat/answer` должен извлекать sentence-level memory-candidates до retrieval/prompt assembly.
- Обоснование: Проект уже вышел за пределы точки, где in-process dictionary можно считать защищаемым personalization-layer. Сохранение памяти через SQLite дает репозиторию inspectable и долговечную границу состояния, а подключение extraction в live answer-path создает минимально жизнеспособную основу для последующего сравнения `RAG-only` и `RAG + memory`.

## D-028 Memory Vector Basis

**Русский**

- Статус: активно
- Решение: Активный vector-basis для memory read/write должен использовать реальный semantic embedding stack, а не deterministic hash placeholder.
- Обоснование: Hopfield-style recall в этом проекте выполняется поверх сохраненных text-embeddings. Поэтому текущая реализация повторно использует active retrieval-embedder для query- и memory-векторов. Hash-based vector-path допустим только как временный test-scaffold и недостаточно силен, чтобы поддерживать научное утверждение о meaningful personalization value от Hopfield-layer.

## D-029 Russian-First Memory Behavior

**Русский**

- Статус: активно
- Решение: Russian-first behavior относится и к memory-layer, а не только к retrieval и generation. Memory extraction и consolidation не должны оставаться English-triggered в активном end-state.
- Обоснование: Bilingual retrieval-layer в сочетании с English-biased memory-layer создал бы вводящий в заблуждение product-behavior gap. Приложение не должно выглядеть multilingual в evidence retrieval и при этом молча уступать в personalization для русскоязычных пользователей.

## D-030 Structured Artifact End-State

**Русский**

- Статус: активно
- Решение: Grounded answering — это закрытый baseline, но не полный structured-generation end-state. Persisted structured artifacts, такие как career plans, skills-gap outputs и wellbeing-oriented plans, по-прежнему остаются обязательными deliverables.
- Обоснование: И project plan, и academic framing предполагают больше, чем просто вопросно-ответный ассистент. Репозиторий не должен позволять текущему answer-first baseline притворяться завершенным structured-output scope.

## D-031 Current Hopfield Implementation Phase

**Русский**

- Статус: активно
- Решение: Текущая поставляемая Hopfield-фаза — это базовая нетренируемая реализация поверх сохраненных embedding-векторов. Recall `top1` реализован как резкий выбор одной лучшей memory, а `topk` реализован как exact top-k masking с последующей перенормировкой softmax-весов.
- Обоснование: Это самое простое академически защищаемое решение, которое все еще соответствует modern Hopfield retrieval-story из зафиксированной в репозитории статьи. Оно сохраняет механизм явным и inspectable до любой optional learned-projection или differentiable `ksoftmax` фазы.
- Основание: В зафиксированной статье one-step modern Hopfield update задается как `x+ = Ξ softmax(βΞᵀ x)`, а k-Hopfield layer — как `X = Ξ ksoftmax(βΞᵀ x0)`. См. `docs/papers/33_Retrieving_k_Nearest_Memori.pdf` и `docs/papers/hopfield_memory.txt`.

## D-032 Memory Extraction Classifier Baseline

**Русский**

- Статус: активно
- Решение: Следующий baseline для memory extraction — это легкий двуязычный sentence-classifier на базе BiLSTM, обучаемый отдельно в `tooling/memory_extraction/`.
- Обоснование: Это сохраняет extraction небольшим, inspectable и академически согласованным с бэкграундом студентки в recurrent networks. Также это сохраняет логическое разделение extraction и Hopfield recall: классификатор решает, должна ли фраза стать memory, а более поздняя type-classification и Hopfield recall остаются отдельными задачами.
- Замечание по реализации: Генерация synthetic corpus для этого classifier должна выполняться как direct standalone GPU tooling с явным локальным контролем модели, а не через OpenAI-compatible runtime-server приложения.
- Замечание по реализации: Первая supervised-задача теперь бинарная: `MEMORY` против `NO_MEMORY`. Fine-grained labels сохраняются в raw synthetic corpus для более поздней type-classification фазы, но первый BiLSTM-baseline не должен сразу решать полную типизацию.
- Замечание по артефактам: Получающиеся synthetic corpora, split manifests, trained model bundles и evaluation reports могут сохраняться в git, когда важна воспроизводимость extraction-baseline.
- Ограничение: Live-backend может пока продолжать использовать heuristic extraction, пока BiLSTM-classifier не будет обучен, оценен и интегрирован. Tooling может поставляться раньше runtime-integration.

## D-033 Memory Extraction Label Schema

**Русский**

- Статус: активно
- Решение: Sentence label schema v1 для memory extraction фиксируется как `NO_MEMORY`, `PREFERENCE`, `CONSTRAINT`, `GOAL` и `AVAILABILITY`.
- Обоснование: Это дает репозиторию небольшой и защищаемый raw-набор меток, напрямую полезный для personalization и последующей memory-lifecycle логики. `NO_MEMORY` дает negative-class, а четыре positive-label cleanly отображаются на более поздние memory category и downstream policy.
- Ограничение: Raw label schema не означает, что первый обучаемый classifier обязан быть пяти-классовым multiclass. Репозиторий теперь использует эти метки как raw supervision, но выводит из них первую бинарную задачу `MEMORY` vs `NO_MEMORY` для начального BiLSTM-baseline.
- Ограничение: Synthetic corpus generation в v1 нацелено только на `ru` и `en`. Mixed-language handling откладывается до тех пор, пока bilingual baseline не будет обучен и измерен.

## D-034 Runtime Sentence Segmentation and Binary Memory Write Integration

**Русский**

- Статус: активно
- Решение: Первая runtime-интеграция обученного BiLSTM-extractor должна работать на детерминированных sentence-like segments, а не на whole user turn и не через еще один LLM extraction-pass.
- Решение: Одно входное сообщение пользователя должно нормализоваться, разбиваться на короткие sentence-like segments через `pySBD`, когда он доступен, и через newline-aware regex-fallback в противном случае, и каждый segment должен независимо классифицироваться как `MEMORY` или `NO_MEMORY`.
- Решение: Принятые segments должны превращаться в отдельные `MemoryItemPayload`, сначала дедуплицироваться внутри запроса через `consolidate_memory_items(...)`, а затем сохраняться через `SqliteMemoryStore.upsert_item(...)`, который остается каноническим normalized-text-per-user слоем дедупликации.
- Решение: Runtime memory extraction должен сначала стадировать request-local candidates, использовать их только как in-memory preview для текущего turn и сохранять их только после того, как запрос завершился non-refusal answer.
- Решение: В binary-only фазе принятые classifier outputs должны использовать coarse runtime-category вроде `user_memory`, сохранять вероятность classifier как `confidence` и держать стабильный default `importance`, пока не появится отдельная phase type-classification.
- Решение: Hopfield-layer не должен реализовывать второй отдельный dedupe-path. Он должен по-прежнему читать уже сохраненный и нормализованный набор `memory_items` и выполнять recall поверх этого списка.
- Обоснование: Classifier по своей природе sentence-level, поэтому whole-turn classification смешивала бы в одно решение несвязанные факты, вопросы и chat-fragments. `pySBD` дает runtime легкий детерминированный bilingual sentence-splitter без еще одного model-call, а regex-fallback сохраняет работоспособность локального app-env, пока зависимости не обновлены. Повторное использование store-level dedupe сохраняет одну каноническую policy persistence вместо того, чтобы дробить логику memory-write по разным модулям. Отложенный commit защищает систему от записи памяти из входов, которые закончились scope-refusal или другим неудовлетворенным исходом.

## D-035 Web UI Stack and Integration Boundary

**Русский**

- Статус: активно
- Решение: Первый реальный web UI должен быть легким TypeScript React-клиентом на базе Vite в каталоге `frontend/`, а не полным template app-stack для AI.
- Решение: Frontend должен напрямую работать с существующим FastAPI-backend по HTTP и считать FastAPI единственным источником истины для chat, plan-generation, retrieval-grounding и поведения памяти.
- Решение: Поверхность frontend v1 намеренно узкая: выбор профиля, чат, citations, “memory used”, structured plan generation и просмотр memory.
- Решение: Локальный backend CORS должен явно разрешать стандартные frontend dev-origins на `127.0.0.1` и `localhost` для портов `5173` и `3000`.
- Обоснование: Репозиторий уже содержит реальную backend-логику и историю evaluation. Добавление второго AI orchestration-layer или большого template app привело бы к дублированию ответственности, размытию границы системы и усложнило бы объяснение и академическую защиту прототипа.
- Ограничение: Первый UI-slice должен оставаться тонким и быстрым для анализа. Save/reload-flow, более богатое state-management и более продвинутая frontend-polish могут появиться позже, но они не должны заменять прямой backend-контракт.

## D-036 Direct Answer Contract: Plain Text With Inline Evidence Refs

**Русский**

- Статус: активно
- Решение: Прямые chat-ответы больше не должны заставлять generator выдавать JSON.
- Решение: Prompt для answer-generation должен запрашивать plain-text с inline-маркерами evidence вроде `[1]` и `[2]`, а backend должен извлекать эти ссылки в структурированный API-response.
- Решение: Структурированный JSON остается уместным для явно структурированных output, таких как career plan, но больше не является предпочтительным контрактом для conversational answer.
- Решение: Для структурированных output, таких как career plan, runtime может использовать детерминированный grounded-template fallback, если локальная small-model не вернула валидный JSON, вместо того чтобы показывать пользователю устранимую runtime-ошибку.
- Решение: Conversational chat-ответы должны звучать как нормальный карьерный коучинг, а не как summary source-дампа. Для exploratory fit-вопросов предпочтительны осторожные варианты и один короткий follow-up question вместо энциклопедического объяснения.
- Решение: Live-backend может заменять free-form answer от small-model детерминированными grounded-guardrails для наиболее проблемных intent-типов, особенно для broad career-fit questions, вопросов о требуемых skills и запросов на external resources, которые текущая ESCO-only evidence-base не может честно удовлетворить.
- Обоснование: Локальный стек small-model надежнее следует коротким инструкциям для plain-text answer, чем жесткому JSON-контракту, а принудительный JSON делал chat-output для пользователя механическим и хрупким.

## D-037 Grounded Support Refusal for Unsupported Requests

**Русский**

- Статус: активно
- Решение: Прототип должен отказывать в явных role-seeking и planning-запросах, если текущий grounded-corpus не показывает достаточно сильного совпадения с поддерживаемой ролью или карьерным переходом.
- Решение: В conversational chat неподдерживаемые explicit role-запросы должны возвращать спокойное refusal-сообщение от ассистента, а не hallucinated generic coaching.
- Решение: В structured planning неподдерживаемые target-role должны завершаться чистым user-facing сообщением о границах scope/support, а не генерацией выдуманного плана.
- Решение: Scope-layer также должен блокировать явно exploitative или illegal work-запросы, а не только crisis-response случаи.
- Обоснование: Текущий ESCO-centered corpus достаточно силен для стандартного grounded career guidance, но не для любого imaginable role-request. Прототип, который честно отказывает в неподдерживаемых запросах, защищать проще, чем систему, которая импровизирует вводящее в заблуждение advice из слабых evidence.

## D-038 Schedule-Aware Career Plans and ICS Export

**Русский**

- Статус: активно
- Решение: Артефакт `career_plan` больше не должен быть только коротким упорядоченным списком шагов. Он также должен нести явные study-preferences, workload-aware schedule metadata и датированные calendar-events, пригодные для прямого `.ics`-экспорта.
- Решение: Первый path calendar-export должен оставаться детерминированным и backend-owned. Frontend может запрашивать `.ics`-файл из сохраненного plan-artifact, но не должен изобретать собственную отдельную scheduling-логику.
- Решение: Текущие scheduling-inputs намеренно минимальны: study start date, preferred time of day, study frequency per week и стабильный default для duration одной сессии.
- Обоснование: Calendar-export можно защищать только тогда, когда сам план уже содержит явные schedule-данные. Детерминированный backend-owned scheduling избегает split-brain plan-model между UI и backend, делает artifact проще для inspection и превращает текущий `career_plan` в реально переиспользуемый structured output, а не в декоративный список шагов.

## D-039 Prototype v1 Closure And Remaining Scope

**Русский**

- Статус: активно
- Решение: Текущий prototype v1 scope теперь считается завершенным.
- Решение: Реализованный v1-scope включает grounded chat, citations, sentence-level memory extraction, persistent user memory, Hopfield-style memory recall, structured career plans, schedule-aware sessions внутри плана, `.ics`-экспорт, local conversation history, memory inspection и UI-facing refusal behavior.
- Решение: Оставшиеся пункты вроде более богатых artifact types, более широкого memory-lifecycle, более глубокой safety-policy, report-grade comparison-output для memory и более сильной real-chat Russian calibration теперь считаются post-v1 refinement work, а не blockers для завершения.
- Обоснование: Репозиторий уже демонстрирует задуманный end-to-end академический product loop. Явная фиксация оставшегося backlog как optional защищает проект от scope creep и делает handoff для студентки более защищаемым.

## D-040 Single-Image Deployment Baseline

**Русский**

- Статус: активно
- Решение: Самый короткий deployable-baseline для текущего прототипа — это один Docker-image, который раздает и собранный frontend, и FastAPI-backend.
- Решение: Frontend должен собираться во время image-creation и затем раздаваться backend-ом из того же runtime-image, а не выноситься в отдельный frontend-container на этапе v1.
- Решение: Deployable-image должен скачивать публичные local runtime model-artifacts во время `docker build`, а не полагаться на то, что неотслеживаемые repo-local model-directories уже существуют в CI.
- Решение: Текущий container-baseline может продолжать использовать существующий dual-process local app-stack runner, чтобы image запускал локальные `llama_cpp.server` и FastAPI вместе внутри одного inspectable unit.
- Решение: Изменяемое runtime-state должно жить вне каталога с отслеживаемыми retrieval-artifacts. Контейнер должен хранить SQLite application-database в отдельном runtime-path, чтобы смонтированные volume не скрывали baked-in FAISS-index.
- Решение: CI должен быть разделен на verification-workflow и container-image-workflow, причем container-image должен собираться и публиковаться только после успешных core CI-checks на `main`.
- Обоснование: Для текущего thesis/demo-scope single-image deployment — это самый быстрый воспроизводимый путь от репозитория до работающего сервера на обычной CPU-VM. Он сохраняет deployment-story понятной, не вводит лишнюю orchestration-сложность и при этом дает реальный deployable artifact через CI.

## Decision Maintenance Rule

**Русский**

Когда меняется активное архитектурное, scope-, stack- или evaluation-решение, обновляйте этот файл в том же изменении.
