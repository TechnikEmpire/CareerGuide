# Student Manual

Last updated: 2026-03-24

## 1. What This Project Is

CareerGuide is an academic proof-of-concept web application for grounded career
guidance. It is not a general-purpose chatbot, not a mobile planner, and not a
pure document search UI.

Its job is to:

- answer career questions using grounded ESCO evidence
- remember stable user preferences from conversation
- recall those memories later through a Hopfield-style mechanism
- generate structured career plans
- turn plans into scheduled study sessions and `.ics` calendar exports

If you need the one-sentence thesis story, use this:

> CareerGuide combines dense retrieval, grounded generation, and a practical
> Hopfield-style memory layer to personalize career guidance without claiming
> to invent a brand-new neural architecture.

## 2. What Is Already Finished

For the current prototype scope, the system is already complete enough to demo
and defend.

Finished core features:

- grounded chat answers
- citations
- sentence-level memory extraction
- persistent memory storage
- Hopfield-style memory recall
- structured career plans
- schedule-aware calendar sessions
- `.ics` export
- web UI with chat, plan, history, and memory views
- refusal behavior for unsupported or out-of-scope requests

What is **not** missing:

- a frontend
- memory persistence
- plan generation
- calendar export
- live backend integration

What remains is optional polish, not missing core product behavior.

## 3. Read These Documents In This Order

If you want to learn the project efficiently, use this order:

1. `README.en.md`
   Why: fast repo-level orientation
2. `docs/STUDENT_MANUAL.en.md`
   Why: this document explains the whole system by feature
3. `docs/STUDENT_MEMORY_GUIDE.en.md`
   Why: the memory subsystem is the student’s strongest academic ownership area
4. `docs/SETUP.en.md`
   Why: environment and local setup
5. `docs/LOCAL_WORKFLOW.en.md`
   Why: how to actually run the stack and evaluation scripts
6. `docs/STATUS.en.md`
   Why: what is finished vs optional
7. `docs/ROADMAP.en.md`
   Why: stage map and what is deferred
8. `docs/DECISIONS.en.md`
   Why: why the architecture looks the way it does

Use the long plan docs in `plan/` only as historical implementation context.
They are no longer the best source for “what the repo does today.”

## 4. Repo Map

These are the main folders you need to understand.

### `backend/`

This is the real application backend.

Important subfolders:

- `backend/app/api/` — FastAPI routes
- `backend/app/services/retrieval/` — retrieval logic
- `backend/app/services/memory/` — memory extraction, persistence, recall
- `backend/app/services/generation/` — prompt building, generator client, plans
- `backend/scripts/` — operator scripts
- `backend/tests/` — regression tests

### `frontend/`

This is the web UI.

Important files:

- `frontend/src/App.tsx` — main application shell and page state
- `frontend/src/api/client.ts` — backend HTTP client
- `frontend/src/components/` — message cards, citations, memory panel
- `frontend/src/styles.css` — current visual system and layout

### `data/`

This holds project data.

- `data/raw/ESCO/` — raw ESCO source dumps
- `data/processed/esco/` — normalized and bilingual ESCO artifacts
- `data/processed/retrieval/` — FAISS retrieval artifacts
- `data/processed/careerguide.db` — SQLite app database

### `tooling/translation/`

One-time preprocessing and translation tooling for ESCO.

### `tooling/memory_extraction/`

Standalone tooling for synthetic memory data generation, classifier training,
and classifier evaluation.

### `docs/`

Current source-of-truth docs.

### `plan/`

Historical working plans. Useful for background, not the first place to look
for the live implementation state.

## 5. Main User-Facing Features

This section explains the app by feature, not by file.

### 5.1 Chat

The user types a question in the frontend. The app sends it to:

- `POST /chat/answer`

The backend then:

1. checks whether the request is in scope
2. stages memory candidates from the user message
3. builds retrieval context from ESCO
4. recalls relevant stored memory
5. builds a grounded prompt
6. either returns a deterministic guardrailed answer or calls the local model
7. persists staged memory only if the request was fulfilled and not refused

Main files:

- `backend/app/api/assistant.py`
- `backend/app/services/assistant_service.py`
- `backend/app/services/retrieval/rag_pipeline.py`
- `backend/app/services/generation/prompt_builder.py`
- `backend/app/services/generation/generator_client.py`
- `backend/app/services/generation/answer_guardrails.py`

### 5.2 Citations

Each answer can show the retrieved chunks that grounded it.

This matters because the project is supposed to be academically defensible.
The student should be able to say:

- what evidence was retrieved
- what evidence was cited
- why the answer should be treated as grounded

Main files:

- `backend/app/services/generation/schemas.py`
- `backend/app/services/retrieval/rag_pipeline.py`
- `frontend/src/components/CitationList.tsx`

### 5.3 Memory

Memory is not free-form magic.

The current system does this:

1. split the user turn into sentence-like segments
2. classify each segment as `MEMORY` or `NO_MEMORY`
3. keep only accepted segments
4. deduplicate them by normalized text
5. persist them in SQLite
6. recall the most relevant memory items later with a Hopfield-style read

Important detail:

- refused requests do **not** persist new memory

Main files:

- `backend/app/services/memory/sentence_split.py`
- `backend/app/services/memory/runtime_classifier.py`
- `backend/app/services/memory/memory_extract.py`
- `backend/app/services/memory/memory_consolidate.py`
- `backend/app/services/memory/memory_store.py`
- `backend/app/services/memory/hopfield_memory.py`

### 5.4 Plans

The plan feature is not just “a long answer.”

It uses:

- a plan request
- retrieved ESCO evidence
- study preferences
- deterministic schedule generation

The backend returns:

- target role
- workload level
- estimated weeks
- ordered steps
- calendar events
- citations

Main files:

- `backend/app/services/generation/plan_guardrails.py`
- `backend/app/services/generation/plan_calendar.py`
- `backend/app/services/generation/esco_grounding.py`
- `backend/app/services/generation/schemas.py`

### 5.5 Calendar Export

Saved plans can be exported as `.ics`.

This is intentionally backend-owned. The frontend does not invent its own
scheduling logic.

Main files:

- `backend/app/api/assistant.py`
- `backend/app/services/generation/plan_calendar.py`
- `frontend/src/api/client.ts`

### 5.6 Conversation History

Conversation history is currently frontend-local, not server-side multi-user
infrastructure.

The frontend stores:

- conversations per `user_id`
- one saved plan per `user_id`

This is kept simple on purpose.

Main file:

- `frontend/src/App.tsx`

### 5.7 Memory Inspection And Deletion

The UI includes a memory view so the student can inspect what the assistant has
remembered.

The user can:

- list memory items
- delete individual memory items

Main files:

- `backend/app/api/memory.py`
- `frontend/src/components/MemoryPanel.tsx`
- `frontend/src/api/client.ts`

### 5.8 Refusal And Scope Handling

The assistant should not happily improvise guidance for unsupported,
exploitative, or clearly out-of-scope requests.

The current behavior is:

- block unsupported role/planning requests
- block exploitative or illegal work requests
- return calm scope/refusal messages in the UI

Main files:

- `backend/app/services/safety/safety.py`
- `backend/app/services/generation/answer_guardrails.py`
- `backend/app/services/assistant_service.py`

## 6. End-To-End Flow By Feature

### 6.1 Answer Flow

Use this when explaining the chat path in a defense or demo.

1. Frontend sends a request from `frontend/src/api/client.ts`.
2. FastAPI receives it in `backend/app/api/assistant.py`.
3. `assistant_service.answer_question()` orchestrates the request.
4. Memory candidates are staged from the question.
5. Retrieval context is built in `rag_pipeline.py`.
6. Memory summary is built with `hopfield_memory.py`.
7. Prompt text is built in `prompt_builder.py`.
8. Guardrails may return a deterministic answer immediately.
9. Otherwise the generator client calls the local model server.
10. The response is normalized into the shared schema.
11. If the answer was fulfilled, staged memory is persisted.
12. The frontend renders the answer, citations, and memory-used summary.

### 6.2 Plan Flow

1. Frontend sends `goal`, `target_role`, and `study_preferences`.
2. FastAPI receives it at `POST /career/plan`.
3. `assistant_service.build_career_plan()` runs retrieval and support checks.
4. The prompt is built with grounded ESCO context.
5. The generator returns structured plan content, or deterministic fallback logic is used.
6. Schedule enrichment turns the plan into dated sessions.
7. The frontend renders steps, schedule, and citations.
8. The frontend can request `.ics` export for the saved plan.

### 6.3 Memory Write Flow

1. User sends a message.
2. The runtime splitter creates sentence-like segments.
3. The BiLSTM classifier scores each segment.
4. Positive memory candidates are staged.
5. They are previewed for the current turn.
6. If the answer is refused, nothing new is persisted.
7. If the answer succeeds, the candidates are upserted into `memory_items`.

This “stage before commit” rule is important and should be mentioned if asked
how memory avoids learning from refused requests.

## 7. API Surface

These are the most important routes.

### `POST /chat/answer`

Main conversational endpoint.

Request:

- `user_id`
- `question`

Response:

- `answer`
- `citations`
- `prompt_preview`
- `memory_summary`
- `response_kind`

### `POST /career/plan`

Structured plan endpoint.

Request:

- `user_id`
- `goal`
- `target_role`
- `study_preferences`

Response:

- role and workload metadata
- ordered plan steps
- calendar events
- citations

### `POST /career/plan/export-ics`

Takes the saved plan payload and returns a downloadable calendar file.

### `GET /memory/list`

Lists persisted memory for one user.

### `DELETE /memory/{memory_id}`

Deletes one memory item for one user.

### `POST /retrieval/preview`

Debug/inspection route that shows ranked retrieved chunks.

### `POST /eval/run-scenarios`

This endpoint still exists only as a placeholder/stub and is not the main
evaluation path today.

## 8. Data And Model Artifacts

### ESCO Source Layer

The current project is grounded mainly in ESCO.

Important artifacts:

- `data/processed/esco/normalized/esco_concepts.en.jsonl`
- `data/processed/esco/normalized/esco_relations.jsonl`
- `data/processed/esco/bilingual/esco_concepts.en_ru.jsonl`

### Retrieval Artifacts

- `data/processed/retrieval/faiss_hnsw.index`
- `data/processed/retrieval/faiss_hnsw_manifest.json`

### App Database

- `data/processed/careerguide.db`

This stores:

- memory rows
- retrieval-side SQLite state used by the backend

### Local Model Artifacts

See `models/README.en.md`.

Important runtime models:

- generator: `Qwen/Qwen3-0.6B`
- embedder: `Qwen/Qwen3-Embedding-0.6B`
- memory classifier bundle: `tooling/memory_extraction/models/bilstm_memory_classifier_binary.pt`

## 9. Tooling You Should Understand

### Translation Tooling

Located in `tooling/translation/`.

Purpose:

- normalize raw ESCO CSV data
- translate the ESCO concept layer into Russian
- produce tracked bilingual artifacts

### Memory Extraction Tooling

Located in `tooling/memory_extraction/`.

Purpose:

- generate synthetic sentence-level memory data
- prepare binary splits
- train the BiLSTM classifier
- evaluate the classifier

Important point:

This tooling is separate from the live backend runtime, even though the
resulting trained bundle is used by the backend.

## 10. How To Run The Project

Use the full instructions in `docs/SETUP.en.md` and `docs/LOCAL_WORKFLOW.en.md`.

The shortest summary is:

1. activate the `careerguide` conda environment
2. build retrieval artifacts if needed
3. start the local backend/generator stack
4. start the frontend

Core commands:

```bash
python -m backend.scripts.build_retrieval_index
python -m backend.scripts.run_local_app_stack --reload
```

Then in another terminal:

```bash
cd frontend
npm install
npm run dev
```

## 11. How To Test The Project

You do not need to memorize every test.

These are the most useful groups:

- `backend/tests/test_app.py` — API behavior
- `backend/tests/test_memory_extract.py` — memory extraction runtime behavior
- `backend/tests/test_memory_store.py` — persistent memory behavior
- `backend/tests/test_hopfield_memory.py` — recall behavior
- `backend/tests/test_plan_calendar.py` — schedule generation and calendar logic
- `backend/tests/test_answer_guardrails.py` — refusal and grounded overrides

For the frontend, the most immediate check is still:

```bash
cd frontend
npm run build
```

## 12. How To Explain The Architecture Academically

Use this explanation:

- The system is a grounded career-guidance assistant.
- Retrieval is dense ANN over processed ESCO data.
- Generation is handled by a small local model behind an OpenAI-compatible API.
- Memory is stored explicitly as persistent user facts/preferences in SQLite.
- Memory recall is performed through a practical Hopfield-style associative step over real embedding vectors.
- The web UI is intentionally thin and calls the backend directly.

Important honesty rule:

Do **not** claim that the current repo already implements the final learned
differentiable Hopfield phase. It does not. The current implementation is the
practical associative-memory phase.

## 13. What Is Still Optional Polish

These items are real, but optional:

- smoother answer style
- broader safety policy
- richer memory lifecycle controls
- more structured artifact types
- better research comparison outputs for memory ablations
- stronger real-chat Russian calibration
- report-oriented debug exports

If someone asks, “What is left?”, this is the correct answer:

> The core system is done. What remains is polish and stronger research-grade
> evidence.

## 14. Where To Look When Something Breaks

### If retrieval fails

Look at:

- `backend/app/services/retrieval/faiss_hnsw.py`
- `backend/scripts/build_retrieval_index.py`
- `data/processed/retrieval/`

### If the local model server fails

Look at:

- `backend/app/services/generation/generator_client.py`
- `backend/app/config.py`
- `backend/scripts/run_local_generation_server.py`

### If memory behavior looks wrong

Look at:

- `backend/app/services/memory/memory_extract.py`
- `backend/app/services/memory/runtime_classifier.py`
- `backend/app/services/memory/memory_store.py`
- `backend/app/services/memory/hopfield_memory.py`

### If plans look wrong

Look at:

- `backend/app/services/generation/plan_guardrails.py`
- `backend/app/services/generation/plan_calendar.py`
- `backend/app/services/generation/esco_grounding.py`

### If the UI looks wrong

Look at:

- `frontend/src/App.tsx`
- `frontend/src/styles.css`
- `frontend/src/components/`

## 15. Final Advice For The Student

If you feel lost, do not start with every file in the repo.

Start with:

1. this manual
2. `frontend/src/App.tsx`
3. `backend/app/services/assistant_service.py`
4. `backend/app/services/retrieval/rag_pipeline.py`
5. `backend/app/services/memory/`
6. `backend/app/services/generation/`

That path will give you the fastest real understanding of how the app works.
