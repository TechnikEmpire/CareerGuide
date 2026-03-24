# Project Status

Last updated: 2026-03-24

### Current Phase

The project is now at **Prototype v1 complete** for the current academic
demonstration scope.

That means the repo already contains:

- a working FastAPI backend
- a working React + Vite web UI
- grounded retrieval over processed ESCO artifacts
- local-model answer generation
- sentence-level memory extraction with a tracked binary BiLSTM bundle
- persistent memory storage plus Hopfield-style memory recall
- structured career plans with schedule metadata and `.ics` export

The remaining work is no longer “missing core product functionality.” It is
optional polish, research-extension work, or later thesis-improvement work.

### What The Prototype Already Does

- Serves a real backend API from `backend/app/`.
- Builds dense retrieval over the tracked ESCO corpus using SQLite + FAISS HNSW.
- Uses `Qwen/Qwen3-Embedding-0.6B` as the active retrieval embedder.
- Uses a local OpenAI-compatible generation server for `Qwen/Qwen3-0.6B`.
- Returns grounded chat answers with citations.
- Stores sentence-level user memory in the SQLite `memory_items` table.
- Extracts memory with the tracked binary BiLSTM classifier bundle.
- Splits user turns into sentence-like segments with `pySBD` preferred and regex fallback.
- Deduplicates memory by normalized text per user.
- Recalls memory through a non-trainable embedding-space Hopfield-style read with `top1` and `topk` modes.
- Refuses unsupported or clearly out-of-scope requests instead of bluffing.
- Generates structured career plans with study preferences, workload metadata, and dated calendar sessions.
- Exports saved plans as `.ics`.
- Ships a real frontend for chat, plan generation, local conversation history, memory inspection, memory deletion, and refusal/scope UI states.

### What Is Verified

- Backend tests cover retrieval, generation contracts, memory extraction,
  memory storage, Hopfield recall, plan scheduling, refusal behavior, and API
  routes.
- The frontend builds successfully under Vite.
- Retrieval artifacts, evaluation fixtures, and scored evaluation outputs are
  present in the repository.
- The schedule-aware plan artifact and `.ics` export path are implemented and
  exercised by tests.

### Authoritative Current Entry Points

For the current live system, start with:

- `README.md`
- `docs/STUDENT_MANUAL.en.md`
- `docs/ROADMAP.md`
- `docs/DECISIONS.md`
- `docs/LOCAL_WORKFLOW.md`
- `docs/SETUP.md`

### What Is Left

Everything below is now **optional polish**, **research extension**, or
**post-v1 refinement**. None of it is required to call the current prototype
functionally complete.

- Better conversational style and prompt polish
- Broader safety-policy coverage beyond the current grounded refusal layer
- Richer memory lifecycle controls such as confirm, archive, or supersede
- Profile-level and artifact-level memory beyond the current `memory_items` slice
- More structured artifacts such as `skills-gap` or `compare-options`, if they remain in scope
- Tracked `RAG-only` vs naive-memory vs Hopfield-memory comparison outputs for the research story
- Stronger real-chat Russian calibration for memory extraction
- Report-quality debug exports and comparison traces
- Cleanup debt such as the FastAPI `on_event` deprecation

### Practical Meaning Of “Done”

For the first thesis/demo version, “done” now means:

1. the student can run the app locally
2. the student can explain the retrieval + memory + plan flow
3. the UI demonstrates the intended product surfaces
4. the remaining backlog is explicitly documented as optional refinement

That condition is now satisfied.

### Current Risks And Honest Caveats

- The assistant is functional but still stylistically rough in places because
  the generator is small and the corpus is ESCO-heavy.
- The live memory extractor is much more real than the old heuristic version,
  but its strongest evidence is still synthetic plus targeted runtime tests
  rather than a large real-chat benchmark.
- The current Hopfield layer is a practical associative-memory mechanism over
  real embedding vectors, not the final learned differentiable phase described
  in the broader research framing.
- The repo contains historical planning documents whose detailed checkpoints are
  older than the current implementation. Use the student manual, roadmap, and
  this status file as the current source of truth.

### Latest Verified Snapshot

- Retrieval stack: SQLite + FAISS HNSW + `Qwen/Qwen3-Embedding-0.6B`
- Generator stack: local OpenAI-compatible server + `Qwen/Qwen3-0.6B`
- Memory store: SQLite `memory_items`
- Memory extraction: sentence-level binary BiLSTM runtime path
- Memory recall: Hopfield-style `top1` and `topk`
- Plan artifact: structured steps + schedule metadata + calendar events + `.ics` export
- Frontend stack: React + Vite + TypeScript
- Frontend surfaces: chat, citations, memory-used display, saved plan, calendar preview, memory list/delete, local history
- Prototype status: complete for the current v1 scope
