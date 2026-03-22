
# Codex Build Plan — Career Guidance Web App with Hybrid RAG + Hopfield-Style Memory

## 0. Purpose

This document is a build plan for Codex. It is intentionally centered on the parts that matter academically and technically:

- corpus selection and ingestion
- retrieval and reranking
- LLM inference choices
- structured generation
- associative memory using a Hopfield-style read
- evaluation against baselines

It deliberately avoids wasting space on generic web infrastructure details.

The target system is a **career guidance and work-life balance assistant** implemented with:

- **Python** for ingestion, retrieval, indexing, orchestration, evaluation, and inference
- **JavaScript** for the web UI and optional browser-side retrieval/inference experiments

The end-user experience should be treated as **Russian-first**. English support and English documentation exist for collaboration, supervision, and technical review.

The thesis claim is not “we invented a new LLM.”  
The claim is:

> A grounded career-guidance assistant can be improved by combining standard RAG with a lightweight Hopfield-style associative memory layer that stores stable user preferences, goals, and constraints.

---

## 1. Final technical decisions

## 1.1 Generator LLM

### Primary model
- **Qwen/Qwen3-0.6B** via GGUF
- exact server artifact: **`Qwen/Qwen3-0.6B-GGUF:Q8_0`**

Why:
- compact enough for a modest Python-hosted server
- stronger generation line than the older Qwen2.5 instruct choice while staying very small
- aligned with the same Qwen3 model generation used by the retrieval stack
- the real intelligence in this system should come from retrieval quality and memory relevance, not from a larger generator
- straightforward to serve with llama.cpp

### Model role in this architecture
Treat the LLM as a **grounded synthesis engine**, not as the system's knowledge base.

The LLM is responsible for:
- synthesizing retrieved passages into short answers
- extracting candidate memory items from user turns
- generating structured plans and task suggestions
- formatting outputs into strict schemas

The LLM is **not** responsible for:
- recalling occupational facts from its parametric memory
- inventing job-market data not present in context
- making scheduling decisions without emitting structured task objects

### Fallback model
- another very small instruct model only as an ultra-light experiment

Use this only if hardware is extremely constrained and accept that output quality will drop.

### CPU-specialized branch
- **Phi-family ONNX model** only if you explicitly decide to optimize for CPU deployment and accept the extra ONNX pipeline complexity.

### Explicit non-goal
Do **not** fine-tune in the MVP.  
Do **not** chase a larger generator model unless retrieval and memory are already strong.  
The novelty is the retrieval + memory architecture, not training.

---

## 1.2 Embedding model

### Primary embedding model
- **Qwen/Qwen3-Embedding-0.6B**

Why:
- multilingual and therefore appropriate for a Russian-first product
- supports more than 100 languages
- keeps the retrieval stack aligned with the current Qwen family direction
- compact enough to be more defensible here than an older heavier multilingual default

### Optional comparison embedding
- **e5-small-v2**

Only use this for an ablation if needed. Do not build the whole project around comparing embedding models.

---

## 1.3 Reranker

### Primary reranker
- **Qwen/Qwen3-Reranker-0.6B**

Why:
- multilingual, which matters for a Russian-first assistant
- practical for top-k reranking in a student-scale pipeline
- aligned with the Qwen embedding choice
- helps reduce semantically-near-but-wrong retrieval hits after dense ANN retrieval

### Reranker operating point
- retrieve top 20 candidates
- rerank to top 6–8
- pass top 4–6 chunks to the generator by default

---

## 1.4 Inference runtime

### Default runtime
- **Python backend + llama.cpp server**
- serve **`Qwen/Qwen3-0.6B-GGUF:Q8_0`**
- call it from FastAPI
- keep generation deterministic and short for structured tasks

### Optional secondary runtime
- **Ollama**
- acceptable if it makes local setup faster for the student
- not preferred for the thesis write-up because llama.cpp is more explicit and reproducible

### Optional browser experiment
- **WebLLM** or equivalent browser inference layer
- use only as a phase-6 experiment
- not required for the core project
- do not let browser inference complexity destabilize the main build

### Initial llama.cpp operating profile
Start with a conservative serving configuration:
- temperature: **0.2**
- top_p: **0.9**
- max generated tokens for normal chat: **256**
- max generated tokens for structured plans: **384–512**
- context assembly target: **<= 4,096 tokens** unless hardware clearly supports more
- enforce JSON-only mode for task extraction and plan generation endpoints

Reason: the model is small and quantized, so stability comes from short prompts, short outputs, tight schemas, and strong retrieval.

---

### 1.4.1 Exact generator artifact and retrieval components

Pin these exact starting components in the repo config:

```yaml
generator:
  runtime: llama.cpp
  model_ref: Qwen/Qwen3-0.6B-GGUF:Q8_0
  chat_format: qwen
  default_max_tokens: 256
  temperature: 0.2
embeddings:
  model_name: Qwen/Qwen3-Embedding-0.6B
reranker:
  model_name: Qwen/Qwen3-Reranker-0.6B
```

Do not replace these components during the initial build. Get the pipeline working first, then run ablations later.

## 1.5 Storage/indexing strategy

### For the MVP
Use:
- **SQLite** for chunk persistence and provenance
- **FAISS HNSW** for dense ANN retrieval
- dense embeddings stored in SQLite tables
- reranking over dense ANN candidates

Reason:
- the corpus is modest but large enough to justify a proper ANN layer
- keeps persistence inspectable while avoiding fake vector-search abstractions
- matches the Russian-first multilingual retrieval requirement

### Do not use initially
- Chroma
- Pinecone
- Qdrant

These are not wrong. They are just unnecessary for the MVP while FAISS HNSW already covers the ANN requirement.

---

## 2. Reference corpus

Build a legally and academically defensible corpus. Separate it into three layers.

## 2.1 Career/occupation layer

### Required sources
1. **O*NET**
2. **ESCO**
3. **Occupational Outlook Handbook (OOH)**

### What to ingest from O*NET
Pull the downloadable database or API-accessible tables for:
- occupations
- task statements
- knowledge
- skills
- abilities
- work activities
- work context
- education/training indicators
- interests / work styles if useful

Create normalized records such as:

```json
{
  "source": "onet",
  "occupation_code": "15-1252.00",
  "occupation_title": "Software Developers",
  "facet": "skills",
  "facet_name": "Programming",
  "importance": 4.12,
  "level": 4.56,
  "text": "Programming — Writing computer programs for various purposes."
}
```

### What to ingest from ESCO
Pull:
- occupations
- skills/competences
- occupation-to-skill relations
- preferred/essential skill relations

Create joinable normalized tables:
- `esco_occupations`
- `esco_skills`
- `esco_links`

### What to ingest from OOH
Pull occupation pages or structured data for:
- summary
- typical duties
- work environment
- education needed
- pay
- job outlook
- similar occupations

OOH gives natural-language career guidance that complements the taxonomic structure of O*NET/ESCO.

---

## 2.2 Career framework layer

### Required source
- **GitLab public career framework / handbook pages**

Ingest:
- role ladders
- level expectations
- behavioral expectations
- scope/responsibility descriptions

Purpose:
- gives the assistant realistic “career progression language”
- useful for answering “how do I move from level X to Y?” questions
- acts as a concrete ladder corpus

---

## 2.3 Wellbeing / work-life layer

### Required sources
- **WHO mental health at work**
- **NIOSH workplace stress**
- **NIOSH Total Worker Health**
- **NIOSH WellBQ**
- **CCOHS** (for Canadian framing where useful)

Ingest:
- recommendations
- intervention categories
- prevention advice
- questionnaire domains
- structured guidance snippets

Purpose:
- enables grounded answers about workload, boundaries, and work-life balance
- gives an evidence-based guardrail against pseudo-therapy behavior

---

## 2.4 Optional source

### Optional Canada-specific labour data
- Canada open employment outlook datasets

Only add this if:
- you want a Canadian regional angle
- you have time to normalize it cleanly

Do not let this delay the main build.

---

## 2.5 Explicit exclusions

Do **not** build the corpus around:
- scraped forum Q&A
- Reddit coaching advice
- Stack Overflow dumps for training
- random blog posts
- generic self-help content

Reason:
- licensing ambiguity
- poor grounding quality
- not thesis-friendly
- makes evaluation less credible

---

## 3. Data normalization and preprocessing

This stage matters. RAG quality will be heavily determined here.

## 3.1 Canonical internal schema

Normalize all corpus items to this document schema:

```json
{
  "doc_id": "string",
  "source": "onet|esco|ooh|gitlab|who|niosh|ccohs",
  "domain": "career|framework|wellbeing",
  "title": "string",
  "section_title": "string",
  "text": "string",
  "url": "string",
  "license_note": "string",
  "jurisdiction": "us|eu|global|canada|company",
  "occupation_codes": ["optional codes"],
  "skill_ids": ["optional ids"],
  "tags": ["career-path", "stress", "promotion", "boundary-setting"],
  "metadata_json": {}
}
```

---

## 3.2 Chunking rules

Chunk text into **300–700 tokens**, with **~80 token overlap**.

Rules:
- keep chunk boundaries aligned with headings/bullets where possible
- never merge unrelated sections just to hit token targets
- preserve source titles and section titles
- attach all metadata to every chunk

For tabular sources like O*NET and ESCO:
- generate compact text records rather than dumping raw tables
- one chunk should capture one coherent fact bundle

Example O*NET-generated chunk:

```text
Occupation: Software Developers
Facet: Skills
Programming — importance 4.12, level 4.56
Critical Thinking — importance 3.88, level 3.75
Complex Problem Solving — importance 3.91, level 3.84
Source: O*NET 30.2
```

---

## 3.3 Deduplication

Perform dedup at two levels:

### Exact dedup
- normalize whitespace
- normalize punctuation
- remove byte-identical duplicates

### Near dedup
- hash normalized text
- compare embedding similarity
- if two chunks are >0.97 cosine and same source/section family, keep one canonical chunk

This prevents chunk spam from multiple mirrored source variants.

---

## 3.4 Metadata enrichment

Add derived metadata during ingest:
- occupational family
- topic tags
- region/jurisdiction
- document type
- confidence tier
- citation display label

Confidence tier example:
- `tier_1`: official public guidance (WHO, O*NET, OOH, ESCO)
- `tier_2`: public framework docs (GitLab)
- `tier_3`: internal/user memory only

At generation time, prefer tier 1 and tier 2 for explicit advice.

---

## 4. Retrieval design

The assistant should use **dense ANN retrieval plus reranking**, not lexical fusion.

## 4.1 Retrieval pipeline

For each user query:

1. classify query intent
2. generate dense query embedding
3. retrieve dense ANN candidates with FAISS HNSW
4. rerank candidates with the Qwen reranker
5. select final context chunks
6. pass context to generator with citations

---

## 4.2 Query intent classifier

Implement a lightweight intent classifier before retrieval.

Supported intents:
- `career_path`
- `skills_gap`
- `role_match`
- `promotion_readiness`
- `learning_plan`
- `work_life_balance`
- `stress_boundary_guidance`
- `general_chat`

Implementation:
- first pass: rules + keyword patterns
- optional second pass: tiny LLM classifier prompt if needed

The intent affects:
- retrieval weighting by domain
- prompt template
- output schema

Example:
- “How do I move from helpdesk to cybersecurity?”  
  -> favor O*NET, ESCO, GitLab ladder chunks
- “I’m overloaded and studying at night is burning me out.”  
  -> favor WHO/NIOSH/CCOHS + memory constraints

---

## 4.3 Dense retrieval

Compute embeddings for:
- all chunks
- all memory items
- incoming user queries

Similarity:
- inner-product search over normalized vectors in **FAISS HNSW**

Start with:
- top 20 dense ANN candidates

---

## 4.4 Reranking

Rerank dense ANN candidates using:
- `Qwen/Qwen3-Reranker-0.6B`

Inputs:
- `(query, candidate_chunk_text)`

Output:
- relevance score

Select:
- top 6 candidates
- trim to 4–6 final chunks based on token budget

Log for evaluation:
- dense score
- rerank score
- final rank

---

## 4.5 Retrieval debugging artifacts

Every assistant run must store:
- original query
- intent label
- dense candidates
- reranked list
- final selected contexts
- final prompt
- model response

This is mandatory for evaluation and debugging.

---

## 5. Generator design

## 5.1 Generation mode

Use the LLM for:
- synthesis
- structured planning
- explanation
- style control

Do **not** use it as the source of raw career facts.

Facts should come from retrieved evidence or stable memory.

---

## 5.2 Prompt structure

Use a fixed prompt contract with these blocks:

1. **system policy**
2. **task instruction**
3. **user profile summary**
4. **retrieved evidence**
5. **retrieved memory**
6. **required JSON schema**
7. **safety reminders**
8. **citation formatting rule**

Example high-level prompt contract:

```text
You are a career guidance assistant.
You must answer using only:
- retrieved evidence
- stable user memory
- cautious general reasoning that does not invent facts

If evidence is weak, say so.

Return valid JSON following the schema exactly.
Then provide a brief natural-language explanation.
```

---

## 5.3 Required output artifacts

Implement these structured outputs first:

### `career_plan`
Fields:
- target_role
- current_state_summary
- strengths
- skill_gaps
- recommended_actions
- timeline_30_days
- timeline_90_days
- work_life_constraints
- evidence_citations
- caveats

### `skills_gap_report`
Fields:
- target_role
- matched_skills
- missing_skills
- partially_met_skills
- recommended_learning_steps
- evidence_citations

### `balance_guidance_note`
Fields:
- issue_summary
- risk_factors
- boundary_recommendations
- work_adjustments
- escalation_note
- evidence_citations

---

## 5.4 Hallucination control rules

The model must not:
- invent salary numbers unless retrieved
- invent legal requirements unless retrieved
- claim medical conclusions
- claim job-market certainty without evidence
- pretend that career ladder examples are universal facts

If asked something unsupported, the correct answer is:
- uncertainty statement
- best-effort grounded guidance
- note about limits
- referral to authoritative sources where appropriate

---

## 6. Associative memory design

This is the main novelty. Keep it honest, small, and measurable.

## 6.1 What memory is for

The memory layer is for **stable user-specific information** that ordinary document RAG will not contain, such as:
- target role
- preferred learning style
- available time per week
- remote-work preference
- dislike of management track
- family/protected-time constraints
- recurring overload triggers
- work-life rules

It is **not** a transcript dump.

---

## 6.2 Memory item schema

Use:

```json
{
  "id": "uuid",
  "user_id": "uuid",
  "memory_type": "goal|preference|constraint|habit|risk|work_life_rule",
  "text": "I can only study 4 hours per week.",
  "normalized_text": "study_limit_hours_per_week=4",
  "source_kind": "profile|assistant_extracted|user_confirmed|artifact",
  "importance": 0.0,
  "confidence": 0.0,
  "embedding": [0.0],
  "created_at": "timestamp",
  "updated_at": "timestamp",
  "is_archived": false
}
```

### Importance
Represents how much the system should preserve this constraint in future planning.

### Confidence
Represents how certain the system is that this memory is real and stable.

---

## 6.3 Memory write policy

Create or update memory only when one of these is true:

1. user explicitly states a stable fact  
2. the same pattern appears repeatedly across interactions  
3. a generated artifact establishes a stable goal and the user accepts it  
4. the user confirms an extracted memory candidate

### Write examples
Store:
- “Target role is cybersecurity analyst”
- “Prefers project-based learning over long courses”
- “Avoid advice requiring relocation”
- “Cannot study on Sundays”
- “Current job already causes late-evening fatigue”

Do not store:
- every transient emotion
- every one-off complaint
- raw sensitive content not needed for personalization
- speculative assistant inferences without confirmation

---

## 6.4 Memory consolidation

Run consolidation after every N interactions.

Consolidation steps:
1. cluster similar memory items by cosine similarity
2. detect conflicts
3. merge duplicates
4. archive stale or superseded items
5. regenerate a concise canonical version

Example:
- “I want to become a backend developer”
- “My goal is backend engineering”
- “I’m aiming for a backend role”

These should become one canonical memory:
- `goal: target_role=backend_engineer`

---

## 6.5 Hopfield-style read mechanism

This should be implemented as a **modern-Hopfield-style associative read**, not as a theatrical claim about building a giant differentiable memory network.

### Definitions

Let:
- `K ∈ R^(n×d)` be the matrix of memory embeddings
- `V ∈ R^(n×m)` be the value representation of memory items  
  (`m` can be text IDs, features, or summary vectors)
- `q ∈ R^d` be the query embedding

Compute:
1. similarity scores  
   `s = (K q) / τ`

2. normalized weights  
   `w = softmax(s)`

3. associative read  
   `r = Σ_i w_i V_i`

Where:
- `τ` is a temperature hyperparameter
- `top_memories = top_n(w)`

### Practical implementation
- use embeddings as keys
- keep `V` as memory metadata + text payloads
- compute a weighted summary over top memories
- return:
  - top memory IDs
  - weights
  - weighted summary string
  - debug scores

### Temperature
Start with:
- `τ = 0.15` or `0.2`

Tune only if retrieval is too flat or too peaky.

---

## 6.6 Query used for memory read

The memory query should embed a concatenation of:
- current user message
- current session intent
- current active plan or target role if known
- current artifact context if present

Do **not** include giant retrieved RAG context when querying memory.
Memory retrieval should remain user-centric, not document-centric.

Example memory query string:

```text
Intent: learning_plan
User goal: transition from helpdesk to cybersecurity
User message: I only have 4 hours each week and I do not want to burn out.
```

---

## 6.7 Memory summary generation

After selecting top memories, build a compact memory summary like:

```text
Stable user context:
- Target role: cybersecurity analyst
- Time limit: 4 study hours/week
- Constraint: Sundays protected for family
- Preference: hands-on/project-based learning
- Risk: evening overload after full workday
```

This summary is what goes into the generator prompt.

Do not dump raw memory rows into the prompt unless debugging.

---

## 6.8 Why this is academically legitimate

The novelty is:
- standard RAG handles external evidence
- associative memory handles stable user-specific constraints
- the experiment tests whether combining them improves personalization and constraint-respect

That is a credible architectural contribution for a class project.

---

## 7. Retrieval + memory joint context assembly

At inference time, assemble context in this order:

1. user query
2. intent classification
3. user profile summary
4. top RAG evidence chunks
5. top associative memories
6. optional artifact history (previous accepted plans)
7. output schema

Context priority:
- hard user constraints override generic planning suggestions
- evidence beats model prior
- recent confirmed memory beats old unconfirmed memory

---

## 8. Safety and scope control

This assistant operates near sensitive topics. Safety must be explicit.

## 8.1 Safety policy

The assistant is allowed to:
- discuss career paths
- discuss skills development
- suggest workload/boundary practices
- summarize public guidance on wellbeing at work

The assistant is not allowed to:
- diagnose mental health conditions
- provide legal advice
- make employment decisions
- rank human worth or suitability in a discriminatory way
- present itself as a therapist, doctor, or lawyer

---

## 8.2 Safety implementation

Implement a lightweight safety layer before generation:

1. classify risky input categories
2. redact or minimize unnecessary sensitive PII in logs
3. if high-risk mental-health/legal content appears:
   - do cautious completion
   - redirect to formal resources
   - avoid confident advice outside scope

Use simple policy-based classification first.  
Do not overbuild guardrail infrastructure.

---

## 8.3 Logging/privacy rules

Do not store raw chat forever by default.

Store:
- prompts used for evaluation
- retrieved chunk IDs
- memory IDs
- outputs
- anonymized debug metadata

Allow memory deletion/archival.

---

## 9. Experimental design

This section is mandatory. It is as important as the system itself.

## 9.1 Research question

Does adding a Hopfield-style associative memory layer improve personalization and constraint-respect in a career guidance assistant compared with RAG-only generation?

---

## 9.2 Baselines

### Baseline A
- no memory
- RAG only

### Baseline B
- naive memory retrieval
- e.g. top-k cosine over memory with no weighted summary

### Proposed
- RAG + Hopfield-style associative read + weighted memory summary

This is better than only comparing RAG vs RAG+memory, because it tests whether the specific memory read mechanism adds anything over naive memory lookup.

---

## 9.3 Scenario set

Create 20–30 scripted scenarios.

Example categories:
- role transition
- promotion readiness
- skill gap under time constraints
- work-life protected-time constraints
- burnout-risk boundary planning
- non-management growth preference
- remote-work preference
- education budget constraints

Example scenario:

```json
{
  "user_profile": {
    "current_role": "helpdesk technician",
    "target_role": "cybersecurity analyst",
    "study_hours_per_week": 4,
    "protected_time": ["Sunday"],
    "learning_preference": "hands-on"
  },
  "query": "Build me a 90-day plan that moves me toward cybersecurity without burning me out."
}
```

---

## 9.4 Metrics

### Human-rated
- personalization
- usefulness
- clarity/actionability
- trustworthiness
- constraint-respect

### Objective
- citation correctness
- number of unsupported claims
- percentage of explicit constraints preserved
- memory relevance precision
- plan completeness
- contradiction count across sessions

---

## 9.5 Ablations

If time allows, run these ablations:
1. no reranker
2. reranker on
3. RAG only
4. RAG + naive memory
5. RAG + Hopfield-style memory

This gives an actual experimental story instead of a demo-only story.

---

## 10. Development stages for Codex

Below is the implementation plan Codex should follow.

## Stage 1 — Corpus acquisition and normalization

### Goal
Build the reference corpus and normalized storage.

### Tasks
1. create `data/raw/` and `data/processed/`
2. add ingestion scripts:
   - `ingest_onet.py`
   - `ingest_esco.py`
   - `ingest_ooh.py`
   - `ingest_gitlab_framework.py`
   - `ingest_wellbeing_docs.py`
3. define canonical document schema
4. normalize all sources into JSONL
5. generate chunk records with metadata
6. deduplicate chunk set

### Acceptance criteria
- all required sources ingest without manual editing
- each chunk has source metadata and citation URL
- chunk counts and per-source stats are printed
- sample queries can be manually traced back to source chunks

### Deliverables
- `corpus_docs.jsonl`
- `corpus_chunks.jsonl`
- `corpus_stats.md`

---

## Stage 2 — Embeddings and retrieval index

### Goal
Make the corpus searchable with dense ANN retrieval plus reranking.

### Tasks
1. create SQLite database schema:
   - `documents`
   - `chunks`
   - `chunk_embeddings`
2. embed all chunks with `Qwen/Qwen3-Embedding-0.6B`
3. build a FAISS HNSW index over normalized vectors
4. implement dense ANN retrieval
5. persist chunk metadata and embedding payloads in SQLite

### Acceptance criteria
- retrieval returns sensible candidates for 10 hand-written test queries
- dense ANN results can be inspected independently
- embeddings can be rebuilt from scratch reproducibly

### Deliverables
- `build_embeddings.py`
- `retrieval.py`
- `tests/test_retrieval_smoke.py`

---

## Stage 3 — Reranking and baseline RAG

### Goal
Create the baseline RAG assistant with structured output.

### Tasks
1. add reranker with `Qwen/Qwen3-Reranker-0.6B`
2. implement end-to-end retrieval pipeline
3. add prompt templates
4. add generator client for llama.cpp server using the pinned `Qwen/Qwen3-0.6B-GGUF:Q8_0` artifact
5. add JSON schema enforcement for:
   - career plan
   - skills gap
   - balance guidance
6. store full run traces

### Acceptance criteria
- assistant answers are grounded in retrieved chunks
- citations point to real source chunks
- JSON output is valid in at least 90% of test runs
- unsupported claims are visibly reduced with reranking on

### Deliverables
- `rag_pipeline.py`
- `generator_client.py`
- `prompt_templates.py`
- `schemas.py`

---

## Stage 4 — User profile and artifact memory

### Goal
Add stable user profile storage before full associative memory.

### Tasks
1. define `users`, `memory_items`, `saved_artifacts`
2. implement profile editing for:
   - target role
   - current role
   - time limits
   - protected time
   - learning preference
3. write accepted generated plans into artifact store
4. inject profile summary into prompts

### Acceptance criteria
- accepted profile fields change generated plans
- saved accepted plans can influence future planning
- memory storage is inspectable and editable

### Deliverables
- `memory_store.py`
- `artifact_store.py`
- `tests/test_profile_injection.py`

---

## Stage 5 — Memory extraction and consolidation

### Goal
Automatically create clean memory items from user interactions.

### Tasks
1. implement memory extraction rules
2. implement confirmation flow for uncertain memories
3. compute embeddings for memory items
4. implement duplicate detection and consolidation
5. add archive/supersede handling

### Acceptance criteria
- repeated stable preferences become one canonical memory
- one-off statements do not pollute memory bank
- conflicts can be surfaced and resolved

### Deliverables
- `memory_extract.py`
- `memory_consolidate.py`
- `tests/test_memory_consolidation.py`

---

## Stage 6 — Hopfield-style memory read

### Goal
Implement the associative memory module.

### Tasks
1. create `hopfield_memory.py`
2. load active memory embeddings into matrix `K`
3. encode memory values `V`
4. embed memory query `q`
5. compute scores, softmax weights, top-n items
6. generate weighted summary
7. attach debug outputs

### Acceptance criteria
- top memories match expected user constraints in scenario tests
- weighted summary is stable and concise
- debug scores are logged for report tables

### Deliverables
- `hopfield_memory.py`
- `tests/test_hopfield_read.py`
- `notebooks/memory_read_debug.ipynb`

---

## Stage 7 — Joint RAG + memory generation

### Goal
Use both retrieved evidence and associative memory in the final assistant.

### Tasks
1. merge RAG context + memory summary into prompt builder
2. add priority rules:
   - explicit user constraints > generic suggestions
   - retrieved evidence > unsupported model priors
3. add comparison switch:
   - RAG only
   - RAG + naive memory
   - RAG + Hopfield memory
4. log which memory items actually affected the answer

### Acceptance criteria
- answers preserve user constraints more reliably than RAG-only baseline
- memory does not overwhelm evidence
- comparison mode works on the same scenario/query pair

### Deliverables
- `assistant_orchestrator.py`
- `prompt_builder.py`
- `tests/test_joint_context.py`

---

## Stage 8 — Safety and refusal behavior

### Goal
Make the assistant safe enough for the domain.

### Tasks
1. add risk classifier for:
   - medical/mental-health escalation
   - legal/employment rights
   - crisis/self-harm redirection
2. add safe completion templates
3. redact or minimize sensitive logging
4. add scope disclaimers for unsupported domains

### Acceptance criteria
- sensitive scenarios produce constrained responses
- assistant does not present itself as therapist/legal authority
- risky outputs are downgraded or redirected appropriately

### Deliverables
- `safety.py`
- `tests/test_safety.py`

---

## Stage 9 — Evaluation harness

### Goal
Generate quantitative and qualitative results for the report.

### Tasks
1. create scenario suite in JSON
2. run all baselines across scenarios
3. log outputs, citations, memory usage, and metrics
4. create evaluator scripts
5. export result tables

### Acceptance criteria
- one command runs the experiment suite
- outputs can be compared side-by-side
- report-ready CSV/Markdown tables are produced

### Deliverables
- `eval/scenarios.json`
- `eval/run_eval.py`
- `eval/score_eval.py`
- `eval/results/*.csv`

---

## Stage 10 — Optional browser inference experiment

### Goal
Test whether a local/private browser mode is feasible **without changing the main system design**. The browser experiment is not allowed to replace the Python + llama.cpp server path.

### Tasks
1. implement capability detection
2. test local embedding in browser
3. test small-model browser inference with WebGPU
4. compare latency, memory use, and first-load size
5. decide whether browser-local mode is demo-only or actually usable

### Acceptance criteria
- experiment report exists
- project does not depend on this mode to function
- clear conclusion is documented

### Deliverables
- `docs/browser_inference_experiment.md`

---

## 11. Repository layout for Codex

```text
project/
  backend/
    app/
      main.py
      api/
        assistant.py
        retrieval.py
        memory.py
        eval.py
      services/
        ingest/
          ingest_onet.py
          ingest_esco.py
          ingest_ooh.py
          ingest_gitlab_framework.py
          ingest_wellbeing_docs.py
        retrieval/
          chunking.py
          embeddings.py
          dense_search.py
          faiss_hnsw.py
          rerank.py
          rag_pipeline.py
        memory/
          memory_store.py
          memory_extract.py
          memory_consolidate.py
          hopfield_memory.py
        generation/
          generator_client.py
          prompt_builder.py
          schemas.py
        safety/
          safety.py
      db/
        models.py
        session.py
        migrations/
      tests/
  frontend/
    src/
      pages/
      components/
      api/
      state/
  data/
    raw/
    processed/
  eval/
    scenarios.json
    run_eval.py
    score_eval.py
  docs/
    browser_inference_experiment.md
```

---

## 12. Prioritized implementation order

If time is limited, implement in this exact order:

1. corpus ingestion
2. dense ANN retrieval
3. reranker
4. baseline RAG structured outputs
5. user profile memory
6. memory extraction
7. Hopfield-style read
8. joint RAG + memory
9. evaluation harness
10. browser-local experiment

Do **not** reverse this order.

---

## 13. Hard de-scope rules

If time gets tight, cut:
1. browser-local LLM inference
2. advanced UI polish
3. multi-turn long context tricks
4. artifact version diffing
5. multiple embedding-model comparisons

Do **not** cut:
- authoritative corpus
- reranker
- structured outputs
- stable memory layer
- evaluation against baselines

---

## 14. Minimal success criteria

The project is successful if it can demonstrate all of the following:

1. answers are grounded in real career/wellbeing sources
2. the assistant can produce a structured 30/90-day career plan
3. the assistant preserves explicit user constraints
4. the memory layer improves personalization over RAG-only baseline
5. the system logs enough artifacts to defend the results in a report

---

## 15. Codex execution notes

When Codex starts implementation:

- prefer explicit, simple Python modules over framework-heavy abstractions
- avoid introducing vector DBs unless retrieval genuinely breaks
- write smoke tests after each stage
- preserve reproducibility:
  - pinned package versions
  - deterministic ingestion scripts
  - saved experiment configs
- keep all memory math transparent and inspectable

The strongest final system is **not** the most complicated one.  
The strongest final system is the one that:
- uses real data,
- retrieves it correctly,
- stores stable user constraints correctly,
- combines evidence and memory coherently,
- and proves that with an evaluation harness.
