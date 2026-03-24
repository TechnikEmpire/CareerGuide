# Codex Build Plan: Web-Based Career Guidance Assistant with Dense ANN RAG + Hopfield-Style Memory

Historical note: this is a preserved working plan. For the current live system,
prefer `docs/STUDENT_MANUAL.en.md`, `docs/STATUS.en.md`, and
`docs/ROADMAP.en.md`.

## 1. Project framing

**Working title:** Career Guidance Assistant with Dense ANN RAG and Associative Memory

**Research framing:**
A web-based career guidance assistant that combines:
- a **small open-weight LLM** for generation,
- **dense ANN-backed RAG** over authoritative career and wellbeing corpora,
- a **small learned Hopfield-style memory module** for persistent user preferences, goals, and constraints.

This aligns with the high-level research document’s recommended scope: use a small open-weight model, authoritative RAG sources, structured outputs, privacy controls, and a modest personalization layer rather than training a large model from scratch. It also matches the implementation document’s advice not to oversell the memory component and to compare **RAG-only** against naive memory lookup and explicit Hopfield recall modes.

The end-user product experience should be treated as **Russian-first**. English documentation and English support remain useful for collaboration and review, but they are not the primary product target.

### Current repo checkpoint

- `Baseline RAG v1 Complete` is already closed for the current scope.
- The active milestone is now `Memory Layer v1 Integrated`.
- The repo now persists user memory through the SQLite `memory_items` table.
- The live `/chat/answer` flow now extracts sentence-level memory candidates through the tracked binary BiLSTM bundle before prompt assembly.
- The repo now also has a trained and evaluated standalone binary BiLSTM memory-extraction baseline under `tooling/memory_extraction/`.
- The next hard comparison is `RAG-only` versus naive-memory versus Hopfield-memory, not another reranker pass.

### Current alignment and active gaps

- Baseline dense retrieval plus local Qwen3 generation is aligned and already defensible.
- The repo has intentionally drifted from the older hybrid-retrieval idea into dense-only live retrieval because measured qrels do not justify reranking right now. Treat lexical retrieval as optional future work, not the critical path.
- The biggest current mismatch is memory quality measurement, not retrieval wiring:
  - memory persistence exists
  - memory write path exists
  - the live extraction path is now sentence-level and bilingual
  - but real-chat Russian quality and threshold calibration are still open
- The second major mismatch is structured artifacts. The plan expects persisted career/wellbeing artifacts, while the repo is still mainly grounded-answer oriented.
- The most important scientific gap is still the missing tracked comparison outputs for naive-memory, Hopfield-`top1`, and Hopfield-`topk` against `RAG-only`.

### Immediate critical-path sequence

1. add tracked `RAG-only`, naive-memory, Hopfield-`top1`, and Hopfield-`topk` comparison artifacts
2. export memory debug artifacts for evaluation and report work
3. run real-chat evaluation and threshold calibration for the live sentence-level extractor
4. add memory lifecycle controls and artifact/profile memory
5. revalidate the recent runtime fixes
6. add the missing safety/refusal layer
7. add later fine-grained type classification only after the binary runtime path is stable

---

## 2. Non-goals

Do **not** spend project time on these unless the core AI path is already working:
- advanced web infra
- multi-tenant auth complexity
- mobile apps
- full offline local-LLM mode in the browser
- fine-tuning
- vector DB infrastructure
- agent frameworks with tool sprawl

The science here is not “can we build a CRUD web app.” The science is:
1. Can a small local/server-side LLM answer career questions well when grounded in curated corpora?
2. Does dense ANN retrieval ground answers well enough on its own?
3. Does a real Hopfield memory layer with explicit `top1`/`topk` recall measurably improve personalization and constraint adherence?

---

## 3. Final stack choices

### 3.1 Required languages
- **Python**: backend, ingestion, indexing, retrieval, memory, evaluation
- **JavaScript/TypeScript**: frontend only

### 3.2 Generation model choice

**Primary model:** `Qwen/Qwen3-0.6B` via GGUF

Use this as the default generation model because it is compact enough for modest student hardware while still giving a stronger generation baseline than the older Qwen2.5 instruct choice. The project should lean on retrieval quality and memory relevance, not a larger generator.

**Fallback option:** another ultra-light instruct model only if hardware becomes extremely constrained

Use this only if hardware is extremely constrained and accept that output quality will drop.

**CPU-specialized alternative:** `Phi-3.5-mini-instruct` or `Phi-3-mini` ONNX path

Use this only if your main requirement becomes **CPU inference first** and you want to test ONNX Runtime or OpenVINO. This is a valid branch, but it adds engineering complexity. For Codex, the default plan should target **llama.cpp-compatible deployment first**, not ONNX-first.

### 3.3 Concrete model decision

For the Codex plan, assume:
- **Generator:** `Qwen/Qwen3-0.6B` via **llama.cpp** server using the pinned GGUF artifact `Qwen/Qwen3-0.6B-GGUF:Q8_0`
- **Embedding model:** `Qwen/Qwen3-Embedding-0.6B`
- **Reranker:** `Qwen/Qwen3-Reranker-0.6B`

This is the simplest defensible trio:
- small enough to run on modest hardware,
- standard for RAG,
- easy to explain academically,
- easy to swap later.

The important nuance is that reranking is not part of the minimal baseline by
default. The current tracked qrels already show that the reranker hurts ranking
quality while adding cost, so the active path is dense-only retrieval.

For the current tracked tuning curve, the practical dense-only elbow is
`top_k=10`, so that is now the active runtime default.

### 3.4 Why not use a larger model?

Because the project’s difficulty is not raw generation power. The difficulty is grounded retrieval, personalized memory, and careful evaluation. A 7B+ model increases latency and hardware demands without changing the research question much.

---

## 4. Data sources to ingest

The attached research document already identified the right corpus families. Keep the corpus narrow and citeable.

### 4.1 Core corpus A: occupations and skills

#### A1. O*NET
Ingest:
- occupation metadata
- detailed work activities
- skills
- knowledge
- abilities
- work styles
- education/training descriptors
- related occupations

**Use for:**
- role descriptions
- skill-gap analysis
- target-role reasoning
- matching a user profile to occupations

#### A2. ESCO
Ingest:
- occupations
- skills/competences
- occupation-skill relations
- broader/narrower taxonomy links
- optional multilingual labels only if needed later

**Use for:**
- skill graph enrichment
- taxonomy normalization
- crosswalking job titles and skills
- supporting Europe-oriented occupation language

#### A3. OOH (Occupational Outlook Handbook)
Ingest:
- occupational profile text
- pay outlook where usable
- growth outlook / job outlook narrative
- typical education and work environment

**Use for:**
- narrative career guidance
- “what does this role look like?” answers
- higher-level summaries and comparison across occupations

### 4.2 Core corpus B: career ladders and progression

#### B1. GitLab engineering career framework / public handbook corpus
Ingest:
- role level pages
- expectations by seniority
- competency descriptions
- progression language

**Use for:**
- “what does senior vs mid-level look like?”
- milestone generation
- 90-day plan structure
- concrete ladder-style career reasoning

This is especially valuable because O*NET and ESCO tell you a lot about occupations and skills, but much less about **ladder progression language**.

### 4.3 Core corpus C: work-life / wellbeing guidance

#### C1. WHO “Mental health at work”
#### C2. NIOSH stress at work documents
#### C3. NIOSH Total Worker Health materials
#### C4. NIOSH WellBQ domains and supporting docs
#### C5. CCOHS workplace mental health / work-life guidance

Ingest only the parts that support:
- workload boundaries
- job stress prevention
- healthy work design
- resource referral
- non-clinical work-life balance guidance

**Use for:**
- boundary-setting suggestions
- workload-safe plan generation
- evidence-based wellbeing references
- guardrails against drifting into therapy/medical advice

### 4.4 Optional corpus D: Canada-specific labor outlook

If you want regional relevance for a Canadian student/user base, add:
- Canada open data employment outlook datasets with narrative ratings and outlook summaries

This is optional for MVP. Add it only after the first RAG loop works.

### 4.5 Data to avoid for MVP

Do **not** build the assistant around:
- Stack Overflow or scraped Q&A corpora
- Reddit-like freeform advice corpora
- large dialogue datasets as main knowledge sources
- unlicensed career blogs

Dialogue datasets are only relevant if later you want tone adaptation. They are not the knowledge base.

---

## 5. How to process the data

### 5.1 Ingestion principle

The corpus is heterogeneous. Do **not** flatten everything into raw text immediately.

Instead, create two layers:

1. **Structured layer**
   - occupation records
   - skill records
   - relation tables
   - ladder levels
   - wellbeing topic categories

2. **Text chunk layer**
   - chunked descriptive text for semantic retrieval and citation

Both layers matter. The structured layer supports deterministic reasoning and better prompting. The chunk layer supports natural-language retrieval.

### 5.2 Canonical internal schema

Create these Python-side entities:

#### `occupation`
- `id`
- `source` (`onet|esco|ooh|gitlab`)
- `external_id`
- `title`
- `summary`
- `category`
- `education_text`
- `outlook_text`
- `work_context_text`
- `raw_json`

#### `skill`
- `id`
- `source`
- `external_id`
- `name`
- `description`
- `skill_type`
- `raw_json`

#### `occupation_skill`
- `occupation_id`
- `skill_id`
- `relation_type`
- `importance_score`
- `level_score`
- `source`

#### `career_level`
- `id`
- `framework_name`
- `role_family`
- `level_name`
- `description`
- `expectations_text`
- `source_url`

#### `source_document`
- `id`
- `source_name`
- `source_type`
- `title`
- `url`
- `license_note`
- `jurisdiction`
- `last_ingested_at`

#### `chunk`
- `id`
- `document_id`
- `chunk_type` (`occupation_desc|skill_desc|wellbeing_guidance|ladder|outlook|policy_style`)
- `title`
- `text`
- `token_count`
- `metadata_json`

#### `chunk_embedding`
- `chunk_id`
- `embedding`

### 5.3 Parsing rules by source

#### O*NET
- Prefer downloading the current database release instead of scraping the website.
- Parse the specific tables into normalized relational tables.
- Build a denormalized occupation profile for retrieval and prompting.
- Generate one “occupation summary text” per occupation for chunking.

#### ESCO
- Use CSV export for the MVP.
- Parse occupations, skills, and occupation-skill mappings.
- Normalize labels and descriptions.
- Keep ESCO IDs so you can later crosswalk or de-duplicate.

#### OOH
- Treat OOH as narrative source text.
- Extract occupation page bodies into one document per role.
- Chunk by headings rather than raw fixed-size only.

#### GitLab career framework
- Treat each ladder page / level page as a structured `career_level` plus chunked text.
- Preserve role family and level labels exactly.

#### Wellbeing corpus
- Keep documents as short, high-quality reference texts.
- Tag sections by topic:
  - `boundaries`
  - `meeting_load`
  - `job_stress`
  - `work_design`
  - `resource_referral`

### 5.4 De-duplication and normalization

You must normalize titles across sources.

Implement:
- lowercase normalization
- punctuation stripping
- synonym map for titles
- skill alias map
- occupation alias map

Examples:
- `software developer` ~ `software engineer`
- `frontend developer` ~ `front-end engineer`
- `data analyst` vs `business intelligence analyst`

Do not over-merge automatically. Keep a conservative alias table.

### 5.5 Chunking strategy

Use source-aware chunking.

#### For narrative docs
- target **350–550 tokens**
- overlap **60–90 tokens**
- split on headings first, then paragraphs
- avoid splitting bullet lists across chunks when possible

#### For structured profiles
Generate synthetic narrative text before chunking.
Example for an occupation:
- title
- summary
- top skills
- work activities
- education notes
- outlook summary

This gives retrieval text that is easier for the embedding model to use than raw table rows.

### 5.6 Embedding strategy

Use `Qwen/Qwen3-Embedding-0.6B` for:
- document chunks
- user queries
- memory items

Store embeddings as float arrays in SQLite for MVP.
Use FAISS HNSW over normalized vectors for ANN retrieval.

### 5.7 Retrieval metadata

Every chunk must store metadata like:
- source name
- source URL
- source type
- occupation title if applicable
- skill tags
- jurisdiction
- ladder level if applicable
- wellbeing topic if applicable

This metadata is critical because the prompt builder should not rely only on raw text.

---

## 6. LLM inference plan

### 6.1 Default inference path

Use **server-side inference in Python**.

This is the default because:
- more reproducible,
- easier to log and evaluate,
- simpler than full browser inference,
- lets you swap models without frontend changes.

### 6.2 Concrete deployment path

Use:
- **local OpenAI-compatible GGUF server** (`llama-cpp-python[server]` preferred)
- GGUF quantized model
- Python backend calls local inference endpoint
- cache local runtime artifacts under repo-local ignored `models/` paths

Recommended quantization starting point:
- `Qwen/Qwen3-0.6B-GGUF:Q8_0`
- start with the official Q8_0 GGUF release and only deviate if evaluation shows a clear reason to change

### 6.3 Prompting mode

Use the model in three bounded modes only:

1. **grounded answer mode**
2. **structured career plan mode**
3. **skills gap / next steps mode**

Do not let the assistant drift into broad open-ended chat. That weakens evaluation and safety.

### 6.4 Output contract

All major assistant outputs should be generated as JSON first.

Required schemas:

#### `career_plan`
- `target_role`
- `current_profile_summary`
- `top_skill_gaps`
- `milestones`
- `weekly_actions`
- `work_life_protections`
- `citations`
- `confidence_notes`

#### `skills_gap_report`
- `target_role`
- `matching_strengths`
- `missing_skills`
- `recommended_projects`
- `recommended_learning`
- `citations`

#### `career_option_comparison`
- `option_a`
- `option_b`
- `fit_rationale`
- `tradeoffs`
- `wellbeing_considerations`
- `citations`

#### `wellbeing_guidance_note`
- `observed_problem`
- `grounded_guidance`
- `work_design_suggestions`
- `resource_referral`
- `citations`

### 6.5 Safety prompt boundaries

System prompt must explicitly require:
- cite retrieved sources,
- distinguish evidence from suggestion,
- never claim legal/medical authority,
- redirect high-risk wellbeing cases to professional or official resources,
- avoid predictive scores like “promotion likelihood” or “burnout risk score”.

---

## 7. RAG design

### 7.1 Core design

Use **dense ANN retrieval** as the baseline:
1. dense query embedding
2. FAISS HNSW candidate search
3. prompt assembly

This matches the current implementation direction and keeps the retrieval stack honest about what is actually doing the search.

### 7.2 Dense retrieval

Use cosine-equivalent inner-product search over normalized `Qwen/Qwen3-Embedding-0.6B` vectors.

For MVP:
- compute and persist all chunk embeddings
- build a FAISS HNSW index
- track the canonical FAISS index and manifest in git for the active retrieval configuration
- allow the build command to restore stale SQLite retrieval rows from the tracked FAISS cache without full re-embedding
- take top 20–30 dense ANN candidates

### 7.3 Reranking

Reranking was evaluated as an ablation using `Qwen/Qwen3-Reranker-0.6B`.

Current outcome:
- it does not improve final recall on the tracked qrels
- it lowers ranking quality at important cutoffs
- it adds substantial runtime cost

So reranking is not part of the active runtime path. Keep the reranker only as
historical ablation context and as a reproducible negative result.

Final prompt context should usually include **5–8 chunks** max.

### 7.4 Retrieval profiles by task

Do not use one retrieval mode for every user request.

#### Query type: “what role is right for me?”
Bias retrieval toward:
- occupation descriptions
- ladder corpus
- outlook summaries

#### Query type: “what skills am I missing?”
Bias retrieval toward:
- occupation-skill mappings
- ESCO/O*NET skills
- ladder expectations

#### Query type: “give me a 90-day plan”
Bias retrieval toward:
- ladder levels
- target-role skills
- wellbeing guidance
- previously saved user plan artifacts

#### Query type: “I’m overloaded / I need balance”
Bias retrieval toward:
- wellbeing guidance
- user memory constraints
- current goals / recent plans

### 7.7 Structured retrieval supplement

The assistant should not rely only on chunk text.

For each query, also compute:
- candidate target occupations from title matching
- candidate target skills from structured tables
- candidate ladder levels from framework labels

Then pass this structured evidence into the prompt separately.

This is one of the highest-value improvements you can make: **RAG over text plus light symbolic retrieval over normalized tables**.

---

## 8. Hopfield-style associative memory design

### 8.1 The honest claim

Do **not** claim that you trained a novel Hopfield network.

Claim this instead:
- user profile and long-term constraints are stored as memory embeddings,
- the system performs a **modern-Hopfield-style associative read** using query-to-memory similarity and softmax weighting,
- this memory signal is injected alongside RAG evidence to improve personalization.

That is honest, academically acceptable, and directly connected to modern attention-style associative retrieval.

### 8.2 What should be stored as memory

Store only **stable, persistent, user-specific facts or preferences**.

Allowed memory categories:
- `goal`
- `target_role`
- `constraint`
- `preference`
- `learning_style`
- `work_life_rule`
- `risk_pattern`
- `recurring_barrier`
- `saved_plan_summary`

Examples:
- “User wants to transition from helpdesk to cybersecurity.”
- “User can study only 4 hours per week.”
- “User prefers project-based learning over video courses.”
- “User does not want relocation-based advice.”
- “User prioritizes work-life balance over maximum salary.”

Do **not** store:
- every utterance
- raw emotional venting by default
- high-risk private details without explicit need

### 8.3 Memory schema

#### `memory_item`
- `id`
- `user_id`
- `memory_type`
- `text`
- `normalized_text`
- `source_kind`
- `importance`
- `confidence`
- `embedding`
- `created_at`
- `updated_at`
- `last_used_at`
- `archived`

### 8.4 Memory write pipeline

When a user submits a message or profile update:

1. detect candidate memory statements
2. classify type
3. normalize text
4. embed normalized text
5. compare against existing same-type memories
6. if similarity high, upsert/update
7. otherwise insert new memory

Use explicit confirmation for important memories where practical.

### 8.5 Memory extraction approach

Start with a **rule + LLM hybrid extractor**.

#### Rule-based patterns
Capture obvious statements:
- “I want to become…”
- “I prefer…”
- “I can only…”
- “I don’t want…”
- “My goal is…”

#### LLM extractor
For less explicit cases, call the small model with a narrow extraction prompt returning JSON:
- `is_memory_candidate`
- `memory_type`
- `normalized_text`
- `confidence`

### 8.6 Hopfield read implementation

Represent memory as:
- key matrix `K` of memory embeddings
- value table `V` of memory text + metadata

Given query embedding `q`:
1. compute similarity `s_i = beta * cos(q, K_i)`
2. compute weights `w_i = softmax(s_i)`
3. return top-N memories by weight
4. optionally compute weighted blended memory summary

This is the full MVP implementation. Keep it one-step. Do not build iterative recurrent dynamics unless you have spare time.

### 8.7 Temperature / beta tuning

Add one exposed parameter:
- `beta` or `temperature`

Low temperature:
- broader memory blending

High temperature:
- sharper retrieval of top memories

Tune this empirically during evaluation.

### 8.8 Memory gating

Do not always inject memory.

Use memory only when:
- top weight exceeds threshold, or
- top 2–3 memories are clearly relevant, or
- query type requires personalization

This prevents irrelevant personalization pollution.

### 8.9 Memory summarization

When multiple relevant memories are retrieved, build a concise memory summary like:

> User is targeting cybersecurity, prefers hands-on learning, has only 4 hours/week, and wants remote-compatible advice.

Then pass both:
- the memory summary
- the individual memory items

into prompt assembly.

### 8.10 What makes this “Hopfield enough” for the class report

The contribution is not that you invented a new neural memory. The contribution is that:
- long-term user constraints are stored as distributed embeddings,
- retrieval uses softmax-weighted associative matching,
- memory affects the final answer measurably,
- you compare against a RAG-only baseline.

That is the academically useful part.

---

## 9. Prompt assembly

### 9.1 Final context sections

Every generation call should assemble:

1. **system instructions**
2. **task schema** requested
3. **user query**
4. **structured user profile**
5. **retrieved memory summary + items**
6. **retrieved RAG evidence**
7. **structured retrieved facts**
8. **output JSON schema**

### 9.2 Prompt discipline

Keep prompts stable. Do not improvise giant dynamic prompts.

One prompt template per task family is enough:
- question answering
- skills gap
- career plan
- option comparison
- wellbeing guidance

### 9.3 Citation handling

Require the model to cite only from retrieved evidence IDs.

Each chunk should have a short handle like:
- `SRC1`
- `SRC2`
- `SRC3`

The model returns citations by these IDs; the application resolves them back to human-readable source metadata.

---

## 10. Backend components for Codex

### 10.1 Python module layout

```text
backend/
  app.py
  config.py
  db.py
  models/
    tables.py
    schemas.py
  ingest/
    ingest_onet.py
    ingest_esco.py
    ingest_ooh.py
    ingest_gitlab_framework.py
    ingest_wellbeing_docs.py
    normalize_titles.py
    build_chunks.py
    build_embeddings.py
  retrieval/
    dense.py
    rerank.py
    faiss_hnsw.py
    query_router.py
  memory/
    extract.py
    store.py
    hopfield.py
    summarize.py
  generation/
    llm_client.py
    prompt_builder.py
    json_schemas.py
    answer.py
  safety/
    pii.py
    escalation.py
    policy.py
  evaluation/
    scenarios.py
    metrics.py
    rag_eval.py
    compare_baselines.py
```

### 10.2 Major backend responsibilities

#### `ingest_*`
- fetch/download datasets
- parse
- normalize
- write tables
- emit chunk docs

#### `build_embeddings.py`
- batch encode chunks
- store vectors

#### `query_router.py`
- classify user query into task family
- choose retrieval profile

#### `faiss_hnsw.py`
- run dense ANN search over persisted embeddings
- return top-k candidates for final context selection

#### `hopfield.py`
- read relevant memory with softmax associative retrieval
- return scored memory items

#### `answer.py`
- build final prompt
- call model
- validate JSON
- attach citations

---

## 11. Development stages for Codex

## Stage 0 — Freeze the scientific scope

### Deliverable
A one-page scope memo fixing:
- supported user journeys,
- allowed outputs,
- chosen datasets,
- chosen models,
- evaluation baselines.

### Decisions to lock
- generator = `Qwen/Qwen3-0.6B` via `Qwen/Qwen3-0.6B-GGUF:Q8_0`
- embedder = `Qwen/Qwen3-Embedding-0.6B`
- reranker artifact retained only for reproducible ablation, not active runtime use
- no fine-tuning in MVP
- no browser-local LLM in MVP
- no vector DB in MVP

### Acceptance test
You can state the exact research question in one sentence:

> Does adding a Hopfield-style associative memory layer to a dense-ANN-RAG career guidance assistant improve personalization and constraint adherence compared with RAG-only generation?

---

## Stage 1 — Build the reference corpus

### Goal
Create a reproducible, legally clean, citeable corpus.

### Tasks
1. Write dataset manifests for each source.
2. Download / snapshot the source files.
3. Parse into normalized tables.
4. Create source documents and chunk records.
5. Record source URLs and license notes.

### Output artifacts
- `data/raw/...`
- `data/processed/...`
- `sqlite` database with normalized tables
- source manifest markdown

### Acceptance test
Given a target role query like “cybersecurity analyst”, the database contains:
- matching occupations,
- matching skill relations,
- at least one narrative outlook/profile source,
- at least one ladder-style source,
- at least one wellbeing source.

---

## Stage 2 — Baseline retrieval without memory

### Goal
Make the RAG pipeline work before touching memory.

### Tasks
1. Persist chunk text and metadata in SQLite.
2. Compute embeddings for all chunks.
3. Implement FAISS HNSW dense similarity search.
4. Return top-k evidence with metadata.
5. Run canonical dense-versus-rerank evaluation and keep only what earns its cost.

### Output artifact
A CLI or endpoint that answers:
- top chunks
- scores
- final ranked evidence list

### Acceptance tests
For 20 hand-written queries:
- at least 70–80% of top-5 chunks should be judged relevant,
- dense-only retrieval should produce stable relevant evidence lists,
- retrieval should finish in acceptable local time.

---

## Stage 3 — LLM grounding and structured outputs

### Goal
Prove the model can answer from sources before personalization exists.

### Tasks
1. Build prompt templates.
2. Add JSON schema validation.
3. Add citation handles.
4. Implement `career_plan`, `skills_gap_report`, and `wellbeing_guidance_note` outputs.
5. Add fallback if model returns malformed JSON.

### Output artifact
A working baseline assistant:
- grounded answer mode
- structured output mode
- citation display

### Acceptance tests
For a set of scripted queries:
- output parses as valid JSON,
- answers mention relevant sources,
- no free-floating uncited claims in structured sections,
- model does not invent unsupported policy/career facts.

### Current repo state

- Grounded answer generation and citation export are real.
- The main remaining drift is that structured artifacts are still behind plan:
  - `career_plan`
  - `skills_gap_report`
  - `wellbeing_guidance_note`
  are not yet first-class persisted outputs in the way the plan intended.

---

## Stage 4 — Memory schema and extraction

### Goal
Create the long-term user memory layer independently from generation.

### Tasks
1. Implement `memory_item` table.
2. Implement rule-based extraction.
3. Implement optional LLM-assisted extractor.
4. Add similarity-based upsert.
5. Add archive/update semantics.

### Output artifact
A memory store that accumulates stable user constraints and goals.

### Acceptance tests
Given a synthetic conversation, the system correctly stores:
- target role,
- time constraints,
- learning preferences,
- work-life rules,
- repeated barriers.

And it should **not** store noisy one-off chat filler.

### Current repo state

- The `memory_items` table and SQLite-backed persistence are now real.
- The live answer path already writes extracted memory before prompt assembly.
- What is still missing is plan-aligned memory quality:
  - bilingual extraction
  - richer typing
  - lifecycle semantics
  - profile/artifact memory beyond the simple constraint path

---

## Stage 5 — Hopfield-style associative read

### Goal
Turn stored memories into an actual retrieval signal.

### Tasks
1. Build memory key matrix from embeddings.
2. Implement cosine similarity + softmax weighting.
3. Return top-N memory items with scores.
4. Generate a short memory summary.
5. Add memory gating threshold.

### Output artifact
A deterministic `memory.retrieve(query_text, context)` component.

### Acceptance tests
For relevant personalized queries, the top memory items are appropriate.
For non-personalized queries, memory injection is minimal or absent.

### Current repo state

- A temporary associative-read scaffold is live.
- The main mismatches are that memory read still uses a deterministic hash embedder instead of the real Qwen embedding model, and the module does not yet expose explicit `top1` and `topk` recall modes.
- That means this stage is only partially aligned until the memory vector space and retrieval policy are upgraded and evaluated.

---

## Stage 6 — Joint RAG + memory generation

### Goal
Inject both retrieval streams into the generator.

### Tasks
1. Extend prompt builder with memory section.
2. Add structured profile summary section.
3. Tune memory vs RAG balance.
4. Expose debug info for evaluation:
   - retrieved chunks
   - retrieved memories
   - model citations

### Output artifact
The full proposed system.

### Acceptance tests
Compared with RAG-only:
- answers respect user constraints more consistently,
- plans better reflect long-term goals,
- irrelevant personalization remains low.

### Current repo state

- The live answer path already injects both retrieval evidence and memory summary.
- The missing part is the actual tracked comparison:
  - `RAG-only`
  - `RAG + naive memory`
  - `RAG + Hopfield top1`
  - `RAG + Hopfield topk`
- Until those outputs exist in the eval workflow, this stage should be treated as active but not closed.

---

## Stage 7 — Safety and governance layer

### Goal
Prevent the system from becoming irresponsible around high-risk guidance.

### Tasks
1. Add basic PII redaction before long-term storage.
2. Add escalation triggers for mental-health/medical/legal content.
3. Add policy rules against deterministic human scoring.
4. Log safety triggers for analysis.

### Output artifact
A small but explicit safety pipeline.

### Acceptance tests
Queries implying crisis, diagnosis, or legal/employment adjudication are redirected or bounded appropriately.

### Current repo state

- This stage is still materially behind the intended end-state.
- The repo has a small scope guard, but not the fuller safety/refusal behavior expected by the plan.

---

## Stage 8 — Evaluation harness

### Goal
Turn the project into a reportable experiment rather than a demo.

### Baselines
- **Baseline A:** no-memory RAG assistant
- **Baseline B:** RAG + naive top-N memory retrieval
- **Proposed:** RAG + Hopfield-style softmax associative memory

### Scenario families
1. target-role transition
2. constrained-study-time planning
3. work-life balance preserving career growth
4. non-relocation constraint
5. hands-on-learning preference
6. repeated overload or burnout-adjacent concern

### Metrics
#### Human-rated
- personalization
- usefulness
- clarity/actionability
- trustworthiness

#### Objective
- constraint adherence
- citation support rate
- retrieval relevance
- consistency across sessions
- JSON validity rate
- safety trigger correctness

### Output artifact
- evaluation notebook / script
- report tables
- ablation charts

### Acceptance tests
You can produce a table showing scenario-by-scenario differences between:
- RAG-only
- RAG + naive memory
- RAG + Hopfield memory

---

## 12. Frontend requirements kept intentionally minimal

The frontend only needs to support:
- profile capture
- chat
- display of structured plans
- plan schedule preview
- plan calendar export
- display of citations
- display of “memory used”
- save/reload plans

That is enough for the scientific core.

Current repo checkpoint for this section:

- the repo now has a real `frontend/` app implemented as a lightweight React + Vite client
- it already supports profile selection, chat, citations, “memory used”, structured plan generation with study preferences, scheduled-plan preview, `.ics` export, memory inspection, local chat history, and save/reload support for one active plan per profile
- it talks directly to the existing FastAPI backend instead of introducing a second AI app layer
- the remaining frontend work after this checkpoint is polish and optional scope expansion, not the minimal scientific-core surface

---

## 13. Concrete first prompts and endpoints

### Backend endpoints
- `POST /chat/answer`
- `POST /career/plan`
- `POST /career/plan/export-ics`
- `POST /career/skills-gap`
- `POST /career/compare-options`
- `POST /memory/upsert`
- `GET /memory/list`
- `POST /eval/run-scenarios`

### First scripted tasks for Codex
1. ingest O*NET into normalized tables
2. ingest ESCO CSV into normalized tables
3. ingest OOH pages into documents/chunks
4. ingest GitLab ladder corpus into `career_level`
5. ingest wellbeing docs into tagged chunks
6. build embeddings for all chunks
7. implement FAISS HNSW retrieval
8. keep reranker only as a preserved ablation path if future evidence warrants revisiting it
9. implement answer pipeline returning JSON with citations
10. implement memory extraction/upsert
11. implement Hopfield-style read and integrate it
12. implement scored evaluation harness on top of tracked qrels and answer-evaluation cases

---

## 14. What to tell Codex to optimize for

When handing this to Codex, keep the instruction pressure on these points:

1. **Correctness over framework cleverness**
2. **Structured data normalization before prompt hacking**
3. **Reproducible ingestion scripts**
4. **Explicit retrieval scoring**
5. **Memory as a separate module with tests**
6. **JSON contracts for outputs**
7. **Evaluation hooks everywhere**

Codex should not spend cycles “designing a modern web architecture.” It should spend cycles on:
- parsers,
- retrieval quality,
- memory logic,
- prompt contracts,
- evaluation code.

---

## 15. Final recommendation

For this project, the cleanest concrete plan is:

- Build a **Python-first backend** around **Qwen/Qwen3-0.6B + Qwen/Qwen3-Embedding-0.6B**.
- Build a **curated authoritative corpus** from **O*NET + ESCO + OOH + GitLab ladder pages + WHO/NIOSH/CCOHS wellbeing guidance**.
- Implement **dense ANN retrieval** over both chunked text and normalized structured tables.
- Keep **reranking** only as a documented negative ablation result unless future evidence materially changes.
- Implement **Hopfield-style memory** as a softmax associative read over user memory embeddings.
- Evaluate **RAG-only vs RAG + memory** as the actual scientific comparison.

That is where the substance is.
