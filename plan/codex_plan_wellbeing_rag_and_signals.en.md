# Codex Plan: Wellbeing RAG and Wellbeing Signal Layer

Last updated: 2026-04-07

## Status of This Document

This is an **active post-v1 extension plan**, not a description of already
implemented runtime behavior.

The current live system is still defined through:

- `docs/STUDENT_MANUAL.en.md`
- `docs/STATUS.en.md`
- `docs/ROADMAP.en.md`
- `docs/DECISIONS.en.md`

This document exists so that the future wellbeing extension does not remain
vague and does not force the implementer to make architectural decisions while
coding.

## Extension Goal

The extension must add four new capability layers to CareerGuide:

1. evidence-backed wellbeing RAG for non-clinical work-life guidance
2. runtime classification signals for emotion, overload, and support intent
3. user-facing wellbeing history with a weekly explicit check-in
4. a safe bridge from wellbeing signals to gentler career guidance behavior

The main product boundary remains unchanged:

- this is a career and work-life assistant
- this is not a therapy product
- this is not a clinical diagnostic tool
- this is not a crisis-response system

## Locked Decisions

- The canonical wellbeing corpus consists of:
  - WHO guidelines and materials on mental health at work
  - WHO workplace mental-health materials
  - CDC/NIOSH Total Worker Health materials
  - NIOSH WellBQ documentation
  - CCOHS workplace mental-health resources
- The corpus is used only for:
  - workload boundaries
  - overload mitigation
  - healthy work design
  - recovery suggestions
  - referral language to official and professional resources
- English source text remains canonical. The Russian layer is produced as a
  derived one-time translation layer with provenance preserved.
- `WHO-5` becomes the main weekly check-in instrument for the user-facing
  wellbeing trend.
- `WellBQ` is used as a domain framework for tagging, retrieval metadata, and
  optional extended assessment, but not as the main frequent UX questionnaire.
- `WHO-5` is not translated manually. The project uses the official Russian
  version.
- WHO/NIOSH/CCOHS guidance that actually enters RAG is translated into a Russian
  derived layer.
- `WellBQ` needs its own translation pass and human review before it is allowed
  into Russian UX.
- The main emotion dataset is `GoEmotions`.
- The default Russian path is:
  - review `ru_go_emotions` for provenance and licensing
  - if the review fails, build a project-owned Russian derivative from
    `GoEmotions` using the existing translation workflow
- The ACL 2024 burnout dataset is used only as weak auxiliary English data, not
  as the source of truth for wellbeing policy.
- The runtime signal stack is fixed as:
  - a multi-label emotion classifier
  - an overload/support-intent classifier
  - a deterministic hybrid risk aggregator
- Runtime emotion buckets are fixed as:
  - `stable`
  - `uncertain`
  - `frustrated`
  - `anxious`
  - `fatigued`
- Final risk bands are fixed as:
  - `green`
  - `amber`
  - `red`
- A mixed retrieval path must bring both career evidence and wellbeing evidence
  when the user message genuinely touches both domains.
- Proprietary burnout instruments are excluded from the baseline. MBI-like
  instruments are not planned without a separate licensing review and a
  separate thesis decision.

## Target Implementation by Stage

### Stage 1. Source Audit and Licensing

Stage goal:

- collect only thesis-defensible and publicly accessible wellbeing sources
- filter out licensing and provenance risks up front
- lock the exact source manifest before preprocessing starts

Sources that must be included in the audit:

- WHO guidelines on mental health at work
- WHO mental health at work pages and related public materials
- CDC/NIOSH Total Worker Health pages and downloadable materials
- CDC/NIOSH WellBQ documentation and supporting materials
- CCOHS healthy workplaces and workplace mental-health resources
- `GoEmotions`
- `ru_go_emotions` only after review
- the ACL 2024 burnout dataset “Inferring Mental Burnout Discourse Across Reddit Communities”

Artifacts that should later be created in this stage:

- `data/raw/wellbeing/`
- `data/raw/wellbeing/who/`
- `data/raw/wellbeing/niosh/`
- `data/raw/wellbeing/ccohs/`
- `data/raw/wellbeing/datasets/`
- `data/processed/wellbeing/manifests/wellbeing_source_manifest.json`
- `data/processed/wellbeing/manifests/wellbeing_license_review.json`

For every source, the manifest must record:

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

Stage decisions:

- Do not include scraped blogs, forums, Reddit advice corpora, generic
  self-help sites, or materials with unclear licenses.
- Store `WHO-5` as an instrument artifact rather than as a normal retrieval
  text chunk.
- Split `WellBQ` into domain metadata and instrument metadata. A full frequent
  questionnaire UX is not required to unblock the wellbeing RAG stage.
- If `ru_go_emotions` does not pass the audit for provenance or reuse clarity,
  classifier work does not stop. The project falls back to its own translated
  variant.

Stage acceptance criteria:

- every external source has a traceable manifest
- no unclear vendor downloads remain in the planned runtime path
- translation policy is decided per source

### Stage 2. Bilingual Preprocessing

Stage goal:

- make the wellbeing corpus reproducible, bilingual, and ready for
  retrieval/indexing
- keep the translation stage separate from the live backend

Planned new tooling paths:

- `tooling/wellbeing/README.ru.md`
- `tooling/wellbeing/README.en.md`
- `tooling/wellbeing/normalize_wellbeing_sources.py`
- `tooling/wellbeing/translate_wellbeing_to_russian.py`
- `tooling/wellbeing/build_who5_instrument.py`
- `tooling/wellbeing/paths.py`

Planned processed artifacts:

- `data/processed/wellbeing/normalized/wellbeing_docs.en.jsonl`
- `data/processed/wellbeing/bilingual/wellbeing_docs.en_ru.jsonl`
- `data/processed/wellbeing/instruments/who5.en_ru.json`
- `data/processed/wellbeing/instruments/wellbq.en_ru.json`
- `data/processed/wellbeing/manifests/wellbeing_translation_manifest.json`
- `data/processed/wellbeing/manifests/wellbeing_preprocessing_stats.json`

The normalized document schema must include at least:

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

`wellbeing_topic` is fixed to a controlled vocabulary:

- `burnout`
- `stress`
- `recovery`
- `boundary_setting`
- `workload_design`
- `sleep_rest`
- `manager_conversation`
- `resource_referral`
- `psychological_safety`

`support_kind` is fixed to a controlled vocabulary:

- `preventive_guidance`
- `self_reflection`
- `work_design`
- `conversation_prompt`
- `resource_referral`
- `questionnaire_context`

Translation stage rules:

- English remains the source of truth.
- Russian text for wellbeing guidance is produced through a one-time
  preprocessing workflow and passes a spot-check review.
- `WHO-5` is assembled from the official English and official Russian versions,
  not from machine translation.
- `WellBQ` for future Russian UX must pass MT + human review + an explicit
  manifest note before it is used in the interface.

Stage acceptance criteria:

- bilingual wellbeing JSONL is reproducibly built from raw sources
- provenance and URLs are not lost
- instrument artifacts are separated from the general RAG corpus

### Stage 3. Retrieval and Index Expansion

Stage goal:

- integrate the wellbeing corpus into the current retrieval stack without
  breaking ESCO-first career guidance
- guarantee balanced retrieval for mixed cases

Planned later code surfaces:

- `backend/app/services/ingest/ingest_wellbeing_docs.py`
- `backend/app/services/retrieval/chunking.py`
- `backend/app/services/retrieval/rag_pipeline.py`
- `backend/scripts/build_retrieval_index.py`
- `backend/scripts/benchmark_retrieval.py`

New retrieval chunk types:

- `wellbeing_guidance`
- `wellbeing_referral`
- `wellbeing_framework`
- `wellbeing_instrument_context`

New retrieval metadata fields:

- `domain` with `career|wellbeing`
- `wellbeing_topic`
- `support_kind`
- `jurisdiction`
- `audience`

The retrieval policy is fixed as follows:

- Career-only prompt:
  - the current dense retrieval baseline remains active
  - wellbeing chunks are not forced into context
- Wellbeing-only prompt:
  - retrieval budget = 8
  - at least 4 chunks must come from `domain=wellbeing`
- Mixed career + wellbeing prompt:
  - total context budget = 10
  - 6 chunks reserved for `domain=career`
  - 4 chunks reserved for `domain=wellbeing`
  - merging follows a deterministic quota-first path, not a winner-takes-all
    path

Prompting and generation constraints:

- if an answer gives workload, burnout, or recovery advice, it must cite at
  least one wellbeing source
- wellbeing guidance must remain job- and work-design grounded
- the assistant must not imitate a therapist and must not diagnose the user

Stage acceptance criteria:

- retrieval can build wellbeing-only and mixed context without displacing ESCO
- the citation layer distinguishes career evidence from wellbeing evidence
- evaluation fixtures cover all three modes: career-only, wellbeing-only, mixed

### Stage 4. Classifier Data and Label Policy

Stage goal:

- add real runtime signals for calmer and more explainable support
- avoid turning the signal layer into opaque general mental-health scoring

Planned model structure:

- Emotion classifier:
  - canonical runtime baseline: compact Russian-friendly transformer encoder
  - training data baseline: `GoEmotions`
  - Russian data path: reviewed `ru_go_emotions` or a repo-owned translated
    `GoEmotions`
- Overload/support-intent classifier:
  - canonical runtime baseline: compact BiLSTM classifier
  - reason: it aligns better with the existing memory-extraction tooling and the
    student’s academic narrative around recurrent models

Training data policy:

- `GoEmotions` is used for general emotion supervision
- the ACL 2024 burnout dataset is used only as auxiliary English burnout
  language data
- the project must collect its own reviewed Russian support-signal dataset
- synthetic augmentation is allowed only as a secondary data source and cannot
  be the only evaluation basis

Planned Russian review dataset:

- a separate tracked Russian spot-check set
- at least four example groups:
  - routine career chat
  - overload complaints
  - burnout-adjacent statements
  - explicit recovery/support requests

The emotion bucket mapping is fixed in advance:

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
  - low-energy overload utterances from the project dataset

The overload/support-intent label space is fixed as:

- `no_support_signal`
- `workload_overload`
- `burnout_language`
- `recovery_request`
- `schedule_friction`

The hybrid risk aggregator must use three input types:

- explicit user check-ins
- classifier outputs from recent chat
- behavioral friction signals from plan/calendar usage

Aggregator rules are fixed as follows:

- `red`
  - latest `WHO-5` score below 28
  - or overload probability >= 0.80 with repeated negative emotion buckets in
    2 of the last 3 user turns
  - or 3 skipped study events in 14 days
- `amber`
  - latest `WHO-5` score from 28 to 52 inclusive
  - or overload probability >= 0.60
  - or 2 skipped study events in 14 days
  - or repeated `frustrated|anxious|fatigued` buckets in 3 of the last 7 user
    turns
- `green`
  - all other cases

Important qualification:

- these bands are not medical conclusions
- they exist only for supportive UX, retrieval choice, and schedule proposals

Stage acceptance criteria:

- the signal stack gives explainable outputs rather than one opaque score
- there is a separate Russian review set
- production risk bands do not depend only on passive inference

### Stage 5. Backend, Storage, and API

Stage goal:

- join wellbeing retrieval, explicit check-ins, and passive observations into an
  inspectable backend path

Planned new modules:

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

`wellbeing_checkins` should later store:

- `id`
- `user_id`
- `instrument`
- `raw_answers_json`
- `raw_score`
- `normalized_score`
- `risk_band`
- `submitted_at`
- `timezone`

`wellbeing_observations` should later store:

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

New public schemas that must later be implemented:

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

New routes that must later be implemented:

- `POST /wellbeing/check-in`
- `GET /wellbeing/summary`

Later changes to chat orchestration:

- `assistant_service.answer_question()` first gathers wellbeing signals
- it then decides whether a mixed retrieval path is needed
- it injects supportive tone constraints into the prompt
- at `amber|red`, it may return wellbeing support actions
- if an active calendar exists, it may return only a proposal preview, but not
  an applied schedule change

Later changes to safety:

- the current crisis/self-harm refusal remains active
- the wellbeing support path adds calm referral language
- the assistant must not give clinical advice, emergency advice, or diagnosis

Stage acceptance criteria:

- explicit and passive wellbeing data live in inspectable SQLite tables
- the API returns a trend, a latest score, and observation history
- the chat path can answer supportively in a non-clinical way

### Stage 6. Evaluation, Documentation, and Release Criteria

Stage goal:

- make the wellbeing extension thesis-defensible and regression-safe

Later evaluation work must include:

- preprocessing tests for manifests, provenance retention, and bilingual outputs
- retrieval evaluation for wellbeing-only, career-only, and mixed prompts
- classifier evaluation:
  - macro F1
  - micro F1
  - AUROC for overload/support detection
  - calibration review
- a tracked Russian spot-check set
- generation evaluation for therapy-style drift avoidance

Planned later test files:

- `backend/tests/test_wellbeing_ingest.py`
- `backend/tests/test_wellbeing_signals.py`
- `backend/tests/test_wellbeing_api.py`
- `backend/tests/test_mixed_retrieval.py`
- `backend/tests/test_wellbeing_guardrails.py`

Documentation updates required at implementation time:

- `docs/DECISIONS.en.md`
- `docs/STATUS.en.md`
- `docs/ROADMAP.en.md`
- `docs/STUDENT_MANUAL.en.md`
- `docs/EVALUATION.en.md`
- `docs/SETUP.en.md` if new tooling steps are required

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

## Practical Outcome

This plan fixes the wellbeing extension as a separate, inspectable, and
bilingual subsystem.

The next plan in this series is expected to build on top of it:

- `codex_plan_active_calendar_and_adaptive_schedule.en.md`

Until this work is implemented, wellbeing remains a planned extension rather
than active runtime behavior.
