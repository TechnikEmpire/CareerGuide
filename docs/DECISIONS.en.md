# Active Decisions

Last updated: 2026-03-24

## D-001 Product Direction

**English**

- Status: active
- Decision: The product is a web-based career-guidance and work-life balance assistant.
- Rationale: This aligns with the repository identity and the student’s academic objective. Mobile and Android planning is out of scope for the active repository direction.

## D-002 Primary Languages

**English**

- Status: active
- Decision: Use Python for backend and AI/data pipeline work. Use JavaScript or TypeScript for frontend work.
- Rationale: The student already knows Python and JavaScript, so the project should remain maximally understandable and maintainable.

## D-003 Generator Runtime

**English**

- Status: active
- Decision: The default generator path is `Qwen/Qwen3-0.6B` served through an OpenAI-compatible local GGUF server, with `llama-cpp-python[server]` as the preferred local implementation.
- Pinned artifact: `Qwen/Qwen3-0.6B-GGUF:Q8_0`
- Rationale: This keeps the generation model compact while moving to the stronger Qwen3 generation line, aligns the generator with the same Qwen3 model family used for retrieval, keeps the backend isolated behind a simple HTTP boundary, and avoids requiring a hand-built external `llama.cpp` binary in the normal setup flow.

## D-004 Retrieval Stack

**English**

- Status: active
- Decision: The retrieval stack uses SQLite to persist chunk text, provenance metadata, and embedding payloads, while dense ANN retrieval is handled by FAISS HNSW.
- Rationale: SQLite remains appropriate for local persistence and inspection, but the vector index itself should be a real ANN structure rather than a database pretending to be one.

## D-005 User Language Priority

**English**

- Status: active
- Decision: The product is Russian-first for end users. English remains a supported language for collaboration, documentation, and review.
- Rationale: This matches the real audience and keeps implementation decisions aligned with the actual demo and thesis context.

## D-006 Memory Novelty Framing

**English**

- Status: active
- Decision: The project's main personalization novelty is a real embedding-space Hopfield memory mechanism with explicit `top1` max-energy recall and `topk` superposed recall modes. The current repo state already includes a basic non-trainable implementation of that mechanism, but it must not be presented as if it already covers the optional learned-projection and differentiable-`ksoftmax` phase.
- Rationale: This connects the student's recurrent-network background, especially LSTM-focused study, to a defensible associative-memory contribution grounded in modern Hopfield literature. The actual claim is not "softmax over memory rows"; it is that the project evaluates explicit Hopfield-like recall regimes as the personalization mechanism over stored embedding vectors.
- Basis: Davydov, Jaffe, Singh, and Bullo, "Retrieving k-Nearest Memories with Modern Hopfield Networks", committed in the repo at `docs/papers/33_Retrieving_k_Nearest_Memori.pdf` and `docs/papers/hopfield_memory.txt`.
- Constraint: Documentation must distinguish clearly between the current non-trainable phase and any later learned-projection phase. The repo may call the current helper a basic Hopfield implementation, but it must not claim differentiable `ksoftmax` or learned memory projections that are not yet built.

## D-007 Evaluation Baseline

**English**

- Status: active
- Decision: The core memory experiment must compare `RAG-only`, `RAG + naive memory retrieval`, `RAG + Hopfield top1 recall`, and `RAG + Hopfield topk recall`.
- Rationale: This isolates whether the specific memory-retrieval policy adds measurable personalization value beyond baseline RAG and beyond a simpler memory lookup. It turns the novelty claim into an actual ablation rather than a naming exercise.

## D-008 Documentation Policy

**English**

- Status: active
- Decision: Authoritative repository documentation must exist in both English and Russian.
- Decision: Where practical, enduring docs should now be maintained as paired language-specific files such as `*.en.md` and `*.ru.md`.
- Decision: The unsuffixed path may remain as a compatibility entrypoint or language selector when that helps preserve stable links.
- Rationale: The project should stay understandable to both technical reviewers and the student, while reducing the maintenance cost and readability problems of very large mixed-language files.

## D-009 Bilingual Scenarios

**English**

- Status: active
- Decision: Evaluation scenarios and other enduring user-facing demo artifacts should include both English and Russian variants where practical.
- Rationale: The repository is bilingual by design, and the demo should show that the product concept can be exercised in both working languages.

## D-010 Retrieval Models

**English**

- Status: active
- Decision: The retrieval stack uses `Qwen/Qwen3-Embedding-0.6B` as the active dense baseline. `Qwen/Qwen3-Reranker-0.6B` is retained only as a scored ablation artifact and is disabled by default in runtime configuration.
- Rationale: This keeps the retrieval stack multilingual and aligned with the current Qwen family. The tracked qrels now show that the reranker hurts ranking quality while adding significant runtime cost, so it has not earned a place in the active path.

## D-011 Progress Tracking

**English**

- Status: active
- Decision: Repository-native progress tracking should live in `docs/ROADMAP.md` and `docs/STATUS.md`.
- Rationale: This gives the project a durable, low-overhead planning and reporting mechanism without needing an external ticketing system.

## D-012 ESCO Artifact Tracking

**English**

- Status: active
- Decision: Raw ESCO vendor downloads should remain ignored by git, while the normalized ESCO concept and relation JSONL artifacts, the bilingual translated ESCO concept corpus, and the preprocessing manifests should be tracked by git.
- Rationale: The raw vendor dump is reproducible from ESCO, but the normalized concept graph, normalized relation graph, bilingual translated corpus, and manifests together form the self-contained academic source layer needed to continue implementation without rerunning preprocessing.

## D-013 ESCO URI And Deduplication

**English**

- Status: active
- Decision: ESCO `conceptUri` values are the canonical concept identifiers used to join bilingual concept text to the ESCO relation graph, and duplicate source concept rows with the same URI should be collapsed during preprocessing by keeping the latest `modifiedDate`.
- Rationale: The URI is the stable graph key. The current ESCO English CSV dump contains a small number of duplicate concept rows that differ only by `modifiedDate`, so preprocessing should remove that vendor-data duplication rather than carrying it into tracked bilingual artifacts.

## D-014 Dense Retrieval Backend

**English**

- Status: active
- Decision: The primary retrieval path should use FAISS HNSW for dense ANN search over the ESCO chunk corpus, while SQLite should persist chunk text, provenance metadata, and stored embedding payloads for that FAISS-backed system.
- Rationale: SQLite is appropriate for local persistence and inspection, but it should not pretend to be the vector index. FAISS HNSW gives the project a proper ANN retrieval layer without introducing heavier external infrastructure.

## D-015 Retrieval Build Workflow

**English**

- Status: active
- Decision: Retrieval artifacts should be built explicitly with `python -m backend.scripts.build_retrieval_index` instead of being seeded lazily on the first user query. When the tracked FAISS cache is already current, the same command may restore stale SQLite retrieval rows without forcing a second full corpus-embedding pass.
- Rationale: The build step is reproducible but expensive enough to deserve an explicit operator command, especially once real Qwen3 embeddings are involved. This keeps runtime behavior predictable, makes retrieval-refresh work auditable, and allows cheap recovery of local SQLite state from the persisted FAISS cache.

## D-016 Tracked Retrieval Cache Artifacts

**English**

- Status: active
- Decision: The persisted FAISS retrieval artifacts `data/processed/retrieval/faiss_hnsw.index` and `data/processed/retrieval/faiss_hnsw_manifest.json` should be tracked by git for the active Qwen3 retrieval configuration. The local SQLite database remains untracked.
- Rationale: The FAISS HNSW build is expensive enough to justify caching in the repository, while the SQLite retrieval table can now be restored cheaply from tracked ESCO source artifacts plus the tracked FAISS cache without repeating the full embedding job.

## D-017 Minimal RAG Baseline

**English**

- Status: active
- Decision: The minimal RAG baseline for this repo is dense retrieval plus grounded generation. Reranking is not part of the active baseline.
- Rationale: The original RAG setup is retrieval followed by generation. The tracked qrels for this repo now show that reranking does not improve final recall and degrades ranking quality, so it should remain outside the active baseline unless future evidence changes.

## D-018 Canonical Evaluation Axes

**English**

- Status: active
- Decision: Retrieval quality should be evaluated with IR-style metrics over labeled relevant chunks, specifically `Recall@k`, `MRR@k`, and `nDCG@k`. Answer quality should be evaluated separately along context relevance, answer faithfulness, and answer relevance.
- Rationale: This separates retriever quality from generation quality, makes top-k and reranker on/off ablations measurable, and aligns the repo with established retrieval evaluation practice plus RAG-specific answer-quality dimensions.

## D-019 Canonical Benchmark Baseline

**English**

- Status: active
- Decision: The canonical retrieval benchmark baseline is CPU-only HNSW search over already-built retrieval artifacts. Dense, reranker, and full-context benchmark modes are explicit opt-in measurements, and the benchmark command must not rebuild retrieval artifacts implicitly.
- Rationale: This separates ANN behavior from model latency, avoids hiding expensive rebuild work inside a benchmark command, and gives the repo a stable default benchmark that is cheap enough to repeat.

## D-020 Canonical Eval Fixtures

**English**

- Status: active
- Decision: Canonical evaluation fixtures must live in tracked repo files. Retrieval judgments should live in `eval/retrieval_qrels.json`, and answer-level evidence cases should live in `eval/answer_eval_cases.json`.
- Rationale: Top-k choices, reranker on/off ablations, and grounded-answer claims cannot be defended from ad hoc conversation memory or console notes. The evaluation basis has to be durable, inspectable, and versioned.

## D-021 Canonical Persisted Retrieval-Eval Outputs

**English**

- Status: active
- Decision: The current scored retrieval-eval state should be persisted in tracked files under `eval/out/`, specifically dense and reranker prediction exports plus their corresponding score reports.
- Rationale: These outputs capture the scored state of the current persisted retrieval index and retrieval settings. They should be durable repo artifacts rather than ephemeral console output, and they now also document the current negative reranker outcome.

## D-022 Current Reranker Outcome

**English**

- Status: active
- Decision: Keep the reranker disabled by default.
- Evidence: The tracked score reports show identical `recall@20` (`0.8611` vs `0.8611`) but worse dense-versus-rerank results for `recall@10` (`0.7963` vs `0.7222`), `ndcg@10` (`0.9304` vs `0.8814`), and `ndcg@20` (`0.9397` vs `0.9048`).
- Rationale: The reranker is more expensive and is currently worse on the tracked qrels, so it should not be part of the active runtime path.

## D-023 Active Dense-Only Retrieval Default

**English**

- Status: active
- Decision: Lock the active dense-only runtime default at `top_k=10`.
- Evidence: The tracked dense-only tuning report shows the practical elbow at `top_k=10`, with `recall@10=0.7963` and `ndcg@10=0.9304`, while `top_k=20` only adds diminishing recall gains (`recall@20=0.8611`, `ndcg@20=0.9397`) at the cost of larger grounded context.
- Rationale: `top_k=10` captures most of the measured retrieval benefit without paying the full prompt-size cost of `top_k=20`, and is therefore the best current dense-only runtime tradeoff.

## D-024 Candidate Pool In Active Dense-Only Mode

**English**

- Status: active
- Decision: Treat `candidate_pool` as inactive in the live dense-only runtime path while reranking remains disabled.
- Evidence: The tracked dense-only tuning output shows identical scores for all tested `candidate_pool` values at the same `top_k`, and the active path no longer reranks candidates.
- Rationale: Leaving `candidate_pool` in the active path would imply a runtime tuning lever that currently does not exist. It should remain only for explicit ablation or future reranker work.

## D-025 Local Runtime Artifact Policy

**English**

- Status: active
- Decision: Local generator and retrieval-runtime model artifacts must be cached under repo-local ignored paths in `models/`, and helper scripts must generate `.env.local` plus the local generation-server config automatically.
- Rationale: The project now depends on local model artifacts for repeatable generation and query-embedding behavior, but those artifacts are too large and machine-specific for Git. Keeping them repo-local, ignored, and script-managed makes the workflow reproducible without pretending the artifacts are source-controlled.

## D-026 Answer-Evidence Citation Attribution

**English**

- Status: active
- Decision: Canonical answer-evidence scoring must rely on explicit model-selected `cited_chunk_ids`. The system must not score the entire retrieved context as if every retrieved chunk had been cited.
- Rationale: Treating the whole retrieval context as citations makes answer-evidence precision collapse as `top_k` grows and turns the metric into a proxy for context width rather than attribution quality. The canonical answer export must therefore preserve explicit citation selection.

## D-027 Persistent Memory Store And Write Path

**English**

- Status: active
- Decision: The active memory store should be SQLite-backed through the `memory_items` table, and the live `/chat/answer` path should extract sentence-level memory candidates before retrieval/prompt assembly.
- Rationale: The project is past the point where an in-process dictionary is a defensible personalization layer. Persisting memory through SQLite gives the repo an inspectable, durable state boundary, and wiring extraction into the live answer path creates the minimum viable basis for later `RAG-only` versus `RAG + memory` evaluation.

## D-028 Memory Vector Basis

**English**

- Status: active
- Decision: The active memory read/write vector basis must use the real semantic embedding stack, not the deterministic hash placeholder.
- Rationale: Hopfield-style recall in this project is performed over stored text embeddings. The current implementation therefore reuses the active retrieval embedder for query and memory vectors. A hash-based vector path is acceptable only as a temporary test scaffold and is not strong enough to support the scientific claim that the Hopfield layer adds meaningful personalization value.

## D-029 Russian-First Memory Behavior

**English**

- Status: active
- Decision: Russian-first behavior applies to the memory layer as well as retrieval and generation. Memory extraction and consolidation should not remain English-triggered in the active end-state.
- Rationale: A bilingual retrieval layer plus an English-biased memory layer would create a misleading product behavior gap. The app must not appear multilingual in evidence retrieval while silently underperforming on personalization for Russian users.

## D-030 Structured Artifact End-State

**English**

- Status: active
- Decision: Grounded answering is the closed baseline, but it is not the full structured-generation end-state. Persisted structured artifacts such as career plans, skills-gap outputs, and wellbeing-oriented plans remain required deliverables.
- Rationale: The project plan and academic framing both assume more than a question-answering assistant. The repo should not let the current answer-first baseline masquerade as the completed structured-output scope.

## D-031 Current Hopfield Implementation Phase

**English**

- Status: active
- Decision: The current shipped Hopfield phase is a basic non-trainable implementation over stored embedding vectors. `top1` recall is implemented as sharp single-memory selection, and `topk` recall is implemented as exact top-k masking plus renormalization over softmax weights.
- Rationale: This is the simplest academically defensible implementation that still matches the modern Hopfield retrieval story in the committed paper. It keeps the mechanism explicit and inspectable before any optional learned-projection or differentiable `ksoftmax` phase.
- Basis: The committed paper defines the one-step modern Hopfield update `x+ = Ξ softmax(βΞᵀ x)` and the k-Hopfield layer `X = Ξ ksoftmax(βΞᵀ x0)`. See `docs/papers/33_Retrieving_k_Nearest_Memori.pdf` and `docs/papers/hopfield_memory.txt`.

## D-032 Memory Extraction Classifier Baseline

**English**

- Status: active
- Decision: The next memory-extraction baseline is a lightweight bilingual sentence classifier implemented as a BiLSTM, trained separately under `tooling/memory_extraction/`.
- Rationale: This keeps extraction small, inspectable, and academically aligned with the student's recurrent-network background. It also keeps extraction logically separate from Hopfield recall: the classifier decides whether a sentence should become memory, while later type classification and Hopfield recall remain separate concerns.
- Implementation note: Synthetic corpus generation for this classifier should run as direct standalone GPU tooling with explicit local model control, not through the app's OpenAI-compatible runtime server.
- Implementation note: The first supervised task is now binary `MEMORY` versus `NO_MEMORY`. Fine-grained labels remain in the raw synthetic corpus for later type-classification work, but the first BiLSTM baseline should not be forced to solve full type assignment on day one.
- Artifact note: The resulting synthetic corpora, split manifests, trained model bundles, and evaluation reports may be persisted in git when reproducibility of the extraction baseline matters.
- Constraint: The live backend may keep using heuristic extraction until the BiLSTM classifier is trained, evaluated, and integrated. Tooling can ship before runtime integration.

## D-033 Memory Extraction Label Schema

**English**

- Status: active
- Decision: The v1 sentence label schema for memory extraction is fixed to `NO_MEMORY`, `PREFERENCE`, `CONSTRAINT`, `GOAL`, and `AVAILABILITY`.
- Rationale: This gives the repo a small, defensible raw label space that is directly useful for personalization and later memory lifecycle work. `NO_MEMORY` provides the negative class, while the four positive labels map cleanly to later memory category and downstream policy.
- Constraint: The raw label schema does not imply that the first trained classifier must be five-way multiclass. The repo now uses those labels as raw supervision while deriving a first binary `MEMORY` vs `NO_MEMORY` task for the initial BiLSTM baseline.
- Constraint: v1 synthetic corpus generation targets only `ru` and `en`. Mixed-language handling is deferred until the bilingual baseline is trained and measured.

## D-034 Runtime Sentence Segmentation and Binary Memory Write Integration

**English**

- Status: active
- Decision: The first runtime integration of the trained BiLSTM extractor should operate on deterministic sentence-like segments, not on whole user turns and not through another LLM extraction pass.
- Decision: One incoming user message should be normalized, split into short sentence-like segments with `pySBD` when available and a newline-aware regex fallback otherwise, and each segment should be classified independently as `MEMORY` or `NO_MEMORY`.
- Decision: Accepted segments should be converted into one `MemoryItemPayload` each, deduplicated first within the request via `consolidate_memory_items(...)`, then persisted through `SqliteMemoryStore.upsert_item(...)`, which remains the canonical normalized-text-per-user dedupe layer.
- Decision: Runtime memory extraction should stage request-local candidates first, use them only as an in-memory preview for the current turn, and persist them only after the request completes with a non-refusal answer.
- Decision: In the binary-only phase, accepted classifier outputs should use a coarse runtime category such as `user_memory`, store classifier probability as `confidence`, and keep a stable default `importance` until a separate type-classification phase exists.
- Decision: The Hopfield layer should not implement a second bespoke dedupe path. It should keep reading the already persisted and normalized `memory_items` set and perform recall over that list.
- Rationale: The classifier is sentence-level by design, so whole-turn classification would mix unrelated facts and questions into one decision. `pySBD` gives the runtime a lightweight deterministic bilingual sentence splitter without another model call, while the regex fallback keeps local app environments usable until dependencies are refreshed. Reusing the existing store-level dedupe keeps one canonical persistence policy instead of fragmenting memory-write logic across multiple modules.

## D-035 Web UI Stack and Integration Boundary

**English**

- Status: active
- Decision: The first real web UI should be a lightweight TypeScript React client built with Vite under `frontend/`, not a full AI-template app stack.
- Decision: The frontend should talk directly to the existing FastAPI backend over HTTP and treat FastAPI as the single source of truth for chat, plan generation, retrieval grounding, and memory behavior.
- Decision: The frontend v1 surface is intentionally narrow: profile selection, chat, citations, “memory used”, structured plan generation, and memory inspection.
- Decision: Local backend CORS should explicitly allow the standard frontend dev origins on `127.0.0.1` and `localhost` for ports `5173` and `3000`.
- Rationale: The repository already contains the real backend logic and evaluation story. Pulling in a second AI orchestration layer or a large template app would duplicate responsibilities, blur the system boundary, and make the prototype harder to explain and defend academically.
- Constraint: The first UI slice should remain thin and fast to inspect. Save/reload flows, richer state management, and advanced frontend polish may follow later, but they should not replace the direct backend contract.

## D-036 Direct Answer Contract: Plain Text With Inline Evidence Refs

**English**

- Status: active
- Decision: Direct chat answers should no longer force the generator to emit JSON.
- Decision: The answer-generation prompt should request plain text with inline evidence markers like `[1]` and `[2]`, while the backend extracts those references into the structured API response.
- Decision: Structured JSON remains appropriate for explicitly structured outputs like career plans, but it is no longer the preferred contract for conversational answers.
- Decision: Structured outputs like career plans may fall back to deterministic grounded templates when the small local model fails to return valid JSON, rather than surfacing avoidable runtime errors to the user.
- Decision: Conversational chat answers should sound like normal career coaching, not like source-dump summaries. Exploratory fit questions should prefer tentative options plus one short follow-up question over encyclopedic explanation.
- Decision: The live backend may override the small-model free-form answer for common failure-prone intents with deterministic grounded guardrails, especially for broad career-fit questions, skill-requirement questions, and external-resource requests that the ESCO-only evidence base cannot honestly satisfy.
- Rationale: The local small-model stack follows rigid JSON less reliably than it follows short plain-text answer instructions, and forcing JSON made the user-visible chat output feel mechanical and brittle.

## D-037 Grounded Support Refusal for Unsupported Requests

**English**

- Status: active
- Decision: The prototype should refuse explicit role-seeking or planning requests when the current grounded corpus does not show a strong enough match for a supported role or transition.
- Decision: In conversational chat, unsupported explicit role requests should return a calm assistant refusal message rather than hallucinated generic coaching.
- Decision: In structured planning, unsupported target roles should fail cleanly with a user-facing scope/support message instead of generating an invented plan.
- Decision: The scope layer should also block clearly exploitative or illegal work requests, not only crisis-response cases.
- Rationale: The current ESCO-centered corpus is strong enough for standard grounded career guidance, but not for every conceivable role request. A prototype that refuses unsupported requests is easier to defend than one that improvises misleading advice from weak evidence.

## D-038 Schedule-Aware Career Plans and ICS Export

**English**

- Status: active
- Decision: The `career_plan` artifact should no longer be only a short ordered list of steps. It should also carry explicit study preferences, workload-aware schedule metadata, and dated calendar events suitable for direct `.ics` export.
- Decision: The first-calendar export path should stay deterministic and backend-owned. The frontend may request an `.ics` file from the saved plan artifact, but it should not invent its own separate scheduling logic.
- Decision: The current scheduling inputs are intentionally minimal: study start date, preferred time of day, study frequency per week, and a stable session-duration default.
- Rationale: A calendar export is only defensible if the plan already contains explicit schedule data. Keeping scheduling deterministic and backend-owned avoids a split-brain plan model between the UI and the backend, makes the artifact easier to inspect, and turns the current `career_plan` into a real reusable structured output rather than a decorative step list.

## D-039 Prototype v1 Closure And Remaining Scope

**English**

- Status: active
- Decision: The current prototype v1 scope is now considered complete.
- Decision: The implemented v1 scope includes grounded chat, citations, sentence-level memory extraction, persistent user memory, Hopfield-style memory recall, structured career plans, schedule-aware plan sessions, `.ics` export, local conversation history, memory inspection, and UI-facing refusal behavior.
- Decision: Remaining items such as richer artifact types, broader memory lifecycle, deeper safety policy, report-grade memory comparison outputs, and stronger real-chat Russian calibration are now post-v1 refinement work rather than blockers for completion.
- Rationale: The repository now already demonstrates the intended end-to-end academic product loop. Keeping the remaining backlog explicitly optional prevents scope creep and makes the student handoff more defensible.

## D-040 Single-Image Deployment Baseline

**English**

- Status: active
- Decision: The shortest deployable baseline for the current prototype is a single Docker image that serves both the built frontend and the FastAPI backend.
- Decision: The frontend should be built during image creation and then served by the backend from the same runtime image, rather than deploying a separate frontend container for v1.
- Decision: The deployable image should download the public local runtime model artifacts during `docker build`, rather than relying on untracked repo-local model directories to exist in CI.
- Decision: The current container baseline may continue to reuse the existing dual-process local app-stack runner so the image starts the local `llama_cpp.server` and FastAPI together inside one inspectable unit.
- Decision: Mutable runtime state should live outside the tracked retrieval-artifact directory. The container should persist the SQLite application database in a separate runtime path so mounted volumes do not hide the baked-in FAISS index.
- Decision: CI should be split into a verification workflow and a container-image workflow, where the container image is built and published only after the core CI checks succeed on `main`.
- Decision: The production host rollout should stay GitHub-driven and SSH-based. After a successful image publish on `main`, a separate deploy workflow should connect to the Linode host, pull `:latest`, and recreate the `app` service in place.
- Rationale: For the current thesis/demo scope, a single-image deployment is the fastest reproducible path from repository to running server on a plain CPU VM. It keeps the deployment story understandable, avoids introducing unnecessary orchestration, and still produces a real deployable artifact through CI.

## Decision Maintenance Rule

**English**

When an active architectural, scope, stack, or evaluation decision changes, update this file in the same change.
