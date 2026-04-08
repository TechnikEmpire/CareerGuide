# План Codex: wellbeing RAG и слой wellbeing-сигналов

Последнее обновление: 2026-04-07

## Статус этого документа

Это **активный план расширения после prototype v1**, а не описание уже
реализованного runtime-path.

Текущая live-система по-прежнему определяется через:

- `docs/STUDENT_MANUAL.ru.md`
- `docs/STATUS.ru.md`
- `docs/ROADMAP.ru.md`
- `docs/DECISIONS.ru.md`

Этот документ нужен для того, чтобы будущая реализация wellbeing-extension не
осталась расплывчатой и не вынуждала implementer-а принимать архитектурные
решения на ходу.

## Цель расширения

Расширение должно добавить в CareerGuide четыре новых capability-слоя:

1. evidence-backed wellbeing RAG для non-clinical work-life guidance
2. runtime-classification signals для эмоций, overload и support-intent
3. user-facing wellbeing history с weekly explicit check-in
4. безопасный мост между wellbeing-сигналами и более щадящим career guidance

Главная граница продукта остается прежней:

- это карьерный и work-life assistant
- это не therapy product
- это не clinical diagnostic tool
- это не crisis-response system

## Зафиксированные решения

- Канонический wellbeing-corpus состоит из:
  - WHO guidelines and materials on mental health at work
  - WHO workplace mental-health materials
  - CDC/NIOSH Total Worker Health materials
  - NIOSH WellBQ documentation
  - CCOHS workplace mental-health resources
- Корпус используется только для:
  - workload boundaries
  - overload mitigation
  - healthy work design
  - recovery suggestions
  - referral language к официальным и профессиональным ресурсам
- English source text остается каноническим. Русский слой создается как
  производный one-time translation layer с сохранением provenance.
- `WHO-5` становится основным weekly check-in instrument для user-facing trend.
- `WellBQ` используется как domain-framework для tagging, retrieval metadata и
  optional extended assessment, но не как основной частый UX-опрос.
- `WHO-5` не переводится вручную. Используется официальная русская версия.
- WHO/NIOSH/CCOHS guidance, которая реально идет в RAG, переводится в русский
  derived-layer.
- `WellBQ` для русского UX требует собственного translation-pass и human review
  до включения в live UI.
- Основной emotion dataset: `GoEmotions`.
- Русский путь по умолчанию:
  - сначала review `ru_go_emotions` по provenance и license
  - если review не проходит, проект делает свой derived Russian layer из
    `GoEmotions` через existing translation workflow
- ACL 2024 burnout dataset используется только как weak auxiliary English data,
  а не как источник истины о wellbeing-policy.
- Runtime signal stack фиксируется как:
  - multi-label emotion classifier
  - overload/support-intent classifier
  - deterministic hybrid risk aggregator
- Runtime emotion buckets фиксируются как:
  - `stable`
  - `uncertain`
  - `frustrated`
  - `anxious`
  - `fatigued`
- Итоговые risk bands фиксируются как:
  - `green`
  - `amber`
  - `red`
- Смешанный retrieval-path обязан приносить и career evidence, и wellbeing
  evidence, если user message реально затрагивает оба домена.
- Proprietary burnout instruments не входят в baseline. MBI-like инструменты
  не планируются без отдельного licensing-review и отдельного thesis decision.

## Целевая реализация по стадиям

### Stage 1. Source Audit and Licensing

Цель стадии:

- собрать только thesis-defensible и publicly accessible wellbeing sources
- заранее отфильтровать license- и provenance-риски
- зафиксировать точный source manifest до preprocessing

Источники, которые должны войти в audit:

- WHO guidelines on mental health at work
- WHO mental health at work pages и связанные public materials
- CDC/NIOSH Total Worker Health pages and downloadable materials
- CDC/NIOSH WellBQ documentation and supporting materials
- CCOHS healthy workplaces and workplace mental-health resources
- `GoEmotions`
- `ru_go_emotions` только после review
- ACL 2024 burnout dataset “Inferring Mental Burnout Discourse Across Reddit Communities”

Что должно быть создано позже на этой стадии:

- `data/raw/wellbeing/`
- `data/raw/wellbeing/who/`
- `data/raw/wellbeing/niosh/`
- `data/raw/wellbeing/ccohs/`
- `data/raw/wellbeing/datasets/`
- `data/processed/wellbeing/manifests/wellbeing_source_manifest.json`
- `data/processed/wellbeing/manifests/wellbeing_license_review.json`

Для каждого источника manifest обязан фиксировать:

- `source_id`
- `title`
- `organization`
- `url`
- `accessed_at`
- `content_type`
- `license_note`
- `jurisdiction`
- `allowed_use`
- `downloaded_artifacts`
- `translation_required`
- `human_review_status`

Решения стадии:

- В corpus не включать scraped blogs, forums, Reddit advice corpora, generic
  self-help sites и материалы с unclear license.
- `WHO-5` хранить отдельно как instrument artifact, а не как обычный retrieval
  text-chunk.
- `WellBQ` разложить на domain metadata и instrument metadata; полный frequent
  questionnaire UX не блокирует wellbeing RAG stage.
- Если `ru_go_emotions` не проходит audit по provenance или reuse clarity,
  classifier work не блокируется: проект переходит на own translated variant.

Acceptance criteria стадии:

- каждый внешний источник имеет traceable manifest
- нет неясных vendor downloads в planned runtime-path
- translation policy определена на уровне каждого источника

### Stage 2. Bilingual Preprocessing

Цель стадии:

- сделать wellbeing-corpus воспроизводимым, bilingual и пригодным для
  retrieval/indexing
- не смешивать translation stage с live backend

Новые planned tooling paths:

- `tooling/wellbeing/README.ru.md`
- `tooling/wellbeing/README.en.md`
- `tooling/wellbeing/normalize_wellbeing_sources.py`
- `tooling/wellbeing/translate_wellbeing_to_russian.py`
- `tooling/wellbeing/build_who5_instrument.py`
- `tooling/wellbeing/paths.py`

Новые processed artifacts:

- `data/processed/wellbeing/normalized/wellbeing_docs.en.jsonl`
- `data/processed/wellbeing/bilingual/wellbeing_docs.en_ru.jsonl`
- `data/processed/wellbeing/instruments/who5.en_ru.json`
- `data/processed/wellbeing/instruments/wellbq.en_ru.json`
- `data/processed/wellbeing/manifests/wellbeing_translation_manifest.json`
- `data/processed/wellbeing/manifests/wellbeing_preprocessing_stats.json`

Нормализованный document schema должен включать как минимум:

- `doc_id`
- `source`
- `title`
- `section_title`
- `text`
- `language`
- `domain`
- `wellbeing_topic`
- `support_kind`
- `jurisdiction`
- `audience`
- `source_url`
- `license_note`
- `instrument_id`
- `translation_status`
- `source_hash`

`wellbeing_topic` фиксируется из ограниченного словаря:

- `burnout`
- `stress`
- `recovery`
- `boundary_setting`
- `workload_design`
- `sleep_rest`
- `manager_conversation`
- `resource_referral`
- `psychological_safety`

`support_kind` фиксируется из ограниченного словаря:

- `preventive_guidance`
- `self_reflection`
- `work_design`
- `conversation_prompt`
- `resource_referral`
- `questionnaire_context`

Правила translation stage:

- English остается source-of-truth.
- Russian text для wellbeing guidance переводится one-time preprocessing
  workflow и проходит spot-check review.
- `WHO-5` собирается из официальной английской и официальной русской версии,
  а не через машинный перевод.
- `WellBQ` для будущего русского UX должен пройти MT + human review + явный
  manifest note до использования в интерфейсе.

Acceptance criteria стадии:

- bilingual wellbeing JSONL воспроизводимо собирается из raw sources
- provenance и URLs не теряются
- instrument artifacts отделены от general RAG corpus

### Stage 3. Retrieval and Index Expansion

Цель стадии:

- встроить wellbeing-corpus в текущий retrieval stack без разрушения ESCO-first
  career guidance
- гарантировать balanced retrieval для mixed cases

Planned code surfaces later:

- `backend/app/services/ingest/ingest_wellbeing_docs.py`
- `backend/app/services/retrieval/chunking.py`
- `backend/app/services/retrieval/rag_pipeline.py`
- `backend/scripts/build_retrieval_index.py`
- `backend/scripts/benchmark_retrieval.py`

Новые retrieval chunk types:

- `wellbeing_guidance`
- `wellbeing_referral`
- `wellbeing_framework`
- `wellbeing_instrument_context`

Новые retrieval metadata fields:

- `domain` with `career|wellbeing`
- `wellbeing_topic`
- `support_kind`
- `jurisdiction`
- `audience`

Retrieval policy фиксируется так:

- Career-only prompt:
  - current dense retrieval baseline остается активным
  - wellbeing chunks не форсятся в context
- Wellbeing-only prompt:
  - retrieval budget = 8
  - минимум 4 chunks должны приходить из `domain=wellbeing`
- Mixed career + wellbeing prompt:
  - общий context budget = 10
  - 6 chunks reserved for `domain=career`
  - 4 chunks reserved for `domain=wellbeing`
  - merge идет deterministic quota-first path, а не “winner takes all”

Prompting and generation constraints:

- если ответ дает workload/burnout/recovery advice, он должен cite хотя бы один
  wellbeing source
- wellbeing guidance должна оставаться job- and work-design grounded
- assistant не должен имитировать психотерапевта и не должен ставить диагнозы

Acceptance criteria стадии:

- retrieval может собрать wellbeing-only и mixed context без вытеснения ESCO
- citation layer различает career и wellbeing evidence
- eval fixtures покрывают all-three modes: career-only, wellbeing-only, mixed

### Stage 4. Classifier Data and Label Policy

Цель стадии:

- добавить реальные runtime-signals для более спокойного и explainable support
- не превращать signal-layer в opaque general mental-health scoring

Планируемая модельная структура:

- Emotion classifier:
  - canonical runtime baseline: compact Russian-friendly transformer encoder
  - training data baseline: `GoEmotions`
  - Russian data path: reviewed `ru_go_emotions` or repo-owned translated
    `GoEmotions`
- Overload/support-intent classifier:
  - canonical runtime baseline: compact BiLSTM classifier
  - reason: ближе к текущему memory-extraction tooling и лучше укладывается в
    академический narrative студентки про recurrent models

Training data policy:

- `GoEmotions` используется для general emotion supervision
- ACL 2024 burnout dataset используется только как auxiliary English burnout
  language data
- проект обязан собрать own reviewed Russian support-signal dataset
- synthetic augmentation допустима только как secondary data source и не может
  быть единственной оценочной базой

Planned Russian review dataset:

- отдельный tracked spot-check set на русском
- минимум четыре группы примеров:
  - routine career chat
  - overload complaints
  - burnout-adjacent statements
  - explicit recovery/support requests

Emotion bucket mapping фиксируется заранее:

- `stable`
  - neutral
  - optimism
  - joy
  - relief
  - gratitude
- `uncertain`
  - confusion
  - realization
  - curiosity
  - surprise
- `frustrated`
  - anger
  - annoyance
  - disappointment
  - disapproval
- `anxious`
  - fear
  - nervousness
  - remorse
  - embarrassment
- `fatigued`
  - sadness
  - grief
  - exhaustion-like reviewed Russian tags
  - low-energy overload utterances from project dataset

Overload/support-intent label space фиксируется так:

- `no_support_signal`
- `workload_overload`
- `burnout_language`
- `recovery_request`
- `schedule_friction`

Hybrid risk aggregator обязан использовать три типа input:

- explicit user check-ins
- classifier outputs from recent chat
- behavioral friction signals from plan/calendar usage

Aggregator rules фиксируются так:

- `red`
  - latest `WHO-5` score below 28
  - or overload probability >= 0.80 with repeated negative emotion buckets in
    2 of last 3 user turns
  - or 3 skipped study events in 14 days
- `amber`
  - latest `WHO-5` score from 28 to 52 inclusive
  - or overload probability >= 0.60
  - or 2 skipped study events in 14 days
  - or repeated `frustrated|anxious|fatigued` buckets in 3 of last 7 user turns
- `green`
  - all other cases

Важная оговорка:

- эти bands не являются медицинскими выводами
- они существуют только для supportive UX, retrieval choice и schedule proposals

Acceptance criteria стадии:

- signal stack дает explainable outputs, а не один opaque score
- есть separate Russian review set
- production risk bands не зависят только от passive inference

### Stage 5. Backend, Storage, and API

Цель стадии:

- соединить wellbeing retrieval, explicit check-ins и passive observations в
  inspectable backend path

Новые planned modules:

- `backend/app/api/wellbeing.py`
- `backend/app/services/wellbeing/__init__.py`
- `backend/app/services/wellbeing/checkins.py`
- `backend/app/services/wellbeing/signals.py`
- `backend/app/services/wellbeing/risk.py`
- `backend/app/services/wellbeing/prompt_support.py`
- `backend/app/services/wellbeing/instruments.py`

Planned database tables:

- `wellbeing_checkins`
  - explicit instrument submissions
- `wellbeing_observations`
  - passive classifier observations tied to chat turns or schedule behavior
- `wellbeing_signal_daily`
  - optional aggregated daily snapshot for graphing speed

`wellbeing_checkins` later should store:

- `id`
- `user_id`
- `instrument`
- `raw_answers_json`
- `raw_score`
- `normalized_score`
- `risk_band`
- `submitted_at`
- `timezone`

`wellbeing_observations` later should store:

- `id`
- `user_id`
- `source` with `chat|checkin|calendar`
- `emotion_bucket`
- `emotion_labels_json`
- `overload_probability`
- `support_intent`
- `risk_band`
- `message_excerpt`
- `observed_at`

Новые public schemas, которые должны быть реализованы позже:

- `WellbeingCheckInRequest`
- `WellbeingCheckInResponse`
- `WellbeingSummaryResponse`
- `WellbeingObservation`

`WellbeingCheckInRequest` later fields:

- `user_id`
- `instrument` default `who5`
- `answers`
- `timezone`

`WellbeingCheckInResponse` later fields:

- `instrument`
- `raw_score`
- `normalized_score`
- `risk_band`
- `recommended_actions`
- `recorded_at`

`WellbeingSummaryResponse` later fields:

- `user_id`
- `current_risk_band`
- `latest_who5_score`
- `rolling_average_score`
- `observations`
- `weekly_points`

`AnswerResponse` later expands with optional fields:

- `wellbeing_signal`
- `wellbeing_support_actions`
- `pending_schedule_proposal`

Новые routes, которые должны быть реализованы позже:

- `POST /wellbeing/check-in`
- `GET /wellbeing/summary`

Changes to chat orchestration later:

- `assistant_service.answer_question()` сначала собирает wellbeing signals
- далее решает, нужен ли mixed retrieval path
- затем inject-ит supportive tone constraints в prompt
- при `amber|red` может вернуть wellbeing support actions
- при наличии active calendar может вернуть только proposal preview, но не
  applied schedule change

Changes to safety later:

- current crisis/self-harm refusal остается активным
- wellbeing support path добавляет calm referral language
- assistant не должен давать clinical advice, emergency advice или diagnosis

Acceptance criteria стадии:

- explicit и passive wellbeing data лежат в inspectable SQLite tables
- API отдает trend, latest score и observation history
- chat path может ответить supportive, но non-clinical способом

### Stage 6. Evaluation, Documentation, and Release Criteria

Цель стадии:

- сделать wellbeing-extension thesis-defensible и regression-safe

Evaluation work later must include:

- preprocessing tests для manifests, provenance retention и bilingual outputs
- retrieval eval для wellbeing-only, career-only и mixed prompts
- classifier eval:
  - macro F1
  - micro F1
  - AUROC for overload/support detection
  - calibration review
- tracked Russian spot-check set
- generation eval for therapy-style drift avoidance

Planned test files later:

- `backend/tests/test_wellbeing_ingest.py`
- `backend/tests/test_wellbeing_signals.py`
- `backend/tests/test_wellbeing_api.py`
- `backend/tests/test_mixed_retrieval.py`
- `backend/tests/test_wellbeing_guardrails.py`

Documentation updates required at implementation time:

- `docs/DECISIONS.ru.md`
- `docs/STATUS.ru.md`
- `docs/ROADMAP.ru.md`
- `docs/STUDENT_MANUAL.ru.md`
- `docs/EVALUATION.ru.md`
- `docs/SETUP.ru.md` if new tooling steps are required

Release criteria for this extension:

1. wellbeing sources are traceable and license-reviewed
2. bilingual preprocessing is reproducible
3. mixed retrieval preserves grounded career guidance
4. `WHO-5` history is visible and explainable
5. passive signals do not auto-diagnose the user
6. safety behavior still refuses crisis scenarios
7. Russian-first UX copy exists for all new wellbeing surfaces

## Explicitly Out of Scope for This Stage

- therapy conversations
- psychiatric diagnosis
- emergency response workflows
- fully autonomous schedule mutation
- proprietary burnout questionnaires
- replacing ESCO as the main career grounding corpus

## External References

- WHO guidelines on mental health at work
  - <https://iris.who.int/bitstream/handle/10665/363177/9789240053052-eng.pdf?sequence=1>
- WHO mental health in the workplace
  - <https://www.who.int/teams/mental-health-and-substance-use/promotion-prevention/mental-health-in-the-workplace>
- WHO-5 Russian version
  - <https://cdn.who.int/media/docs/default-source/mental-health/who-5_russian.pdf>
- CDC NIOSH Total Worker Health
  - <https://www.cdc.gov/niosh/twh>
- CDC NIOSH WellBQ
  - <https://www.cdc.gov/niosh/twh/php/wellbq/index.html>
- CCOHS healthy workplaces employer resources
  - <https://www.ccohs.ca/healthyworkplaces/employers>
- GoEmotions
  - <https://research.google/pubs/goemotions-a-dataset-of-fine-grained-emotions/>
- ACL 2024 burnout auxiliary dataset
  - <https://aclanthology.org/2024.nlp4pi-1.21/>

## Практический итог

Этот план фиксирует wellbeing-extension как отдельную, inspectable и
двуязычную подсистему.

Следующий план в этой серии должен строиться поверх него:

- `codex_plan_active_calendar_and_adaptive_schedule.ru.md`

Пока эта стадия не реализована, wellbeing remains a planned extension rather
than active runtime behavior.
