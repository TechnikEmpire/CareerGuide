# Project Roadmap

Last updated: 2026-04-28

### Purpose

This file is the stage map for the repository.

Use it to answer:

- what major phases exist
- which phases are already complete for the current prototype
- which items are now optional polish instead of critical-path work

For a more narrative current-state snapshot, use `docs/STATUS.md`.

### Status Legend

- `completed` = implemented and accepted for the current prototype scope
- `optional` = explicitly deferred polish, extension, or later research work

### Roadmap

| Stage | Status | Summary |
| --- | --- | --- |
| 0. Repo foundation and governance | completed | Canonical repo guidance, decisions tracking, setup docs, engineering standards, and implementation governance are in place. |
| 1. Corpus acquisition and normalization | completed | ESCO ingestion, normalization, bilingual translation, and tracked preprocessing artifacts are in place. |
| 2. Embeddings and retrieval index | completed | The repo now uses SQLite-persisted chunk data plus FAISS HNSW retrieval artifacts with explicit build scripts. |
| 3. Baseline RAG retrieval | completed | Dense-only retrieval is measured, benchmarked, and locked as the active baseline for the current scope. |
| 4. LLM grounding and structured generation | completed | Grounded answer generation, explicit citations, structured plan generation, and deterministic fallbacks are implemented. |
| 5. User memory persistence | completed | The live system persists user memory in SQLite and exposes it through backend and frontend inspection flows. |
| 6. Memory extraction and consolidation | completed | Sentence-level binary BiLSTM extraction, preferred `pySBD` segmentation, and normalized-text dedupe are live. |
| 7. Hopfield-style memory read | completed | A practical non-trainable embedding-space Hopfield recall with `top1` and `topk` modes is wired into the live answer path. |
| 8. Joint RAG + memory generation | completed | The live assistant combines dense retrieval with persisted memory and grounded conversational guardrails. |
| 9. Safety and scoped guidance behavior | completed | The prototype blocks exploitative/out-of-scope requests, keeps unsupported plans grounded, and gives limited caveated chat guidance for legitimate weakly grounded roles. |
| 10. Evaluation baseline | completed | Retrieval qrels, answer-eval fixtures, scoring scripts, benchmark outputs, and core regression tests exist for the current prototype scope. |
| 11. Web UI v1 | completed | The frontend now covers chat, citations, memory, saved plans, study preferences, scheduled sessions, local history, and `.ics` export. |
| 12. Deployment baseline | completed | The repo now builds, publishes, and automatically deploys a single-image container that serves the frontend and backend together and bakes in the public local runtime models. |
| 13. Optional post-v1 refinement | optional | Everything that remains is now polish, research extension, or thesis-strengthening work rather than missing product core. |

### Optional Polish Backlog

The following items remain valuable, but they are **not** blockers for the
current end-to-end prototype:

- richer conversational polish and better answer style
- broader safety policy and more nuanced refusal coverage
- profile-level and artifact-level memory beyond the current `memory_items` model
- lifecycle behavior for memory such as confirm, archive, and supersede
- more structured artifact types such as `skills-gap` and `compare-options`
- tracked `RAG-only` vs naive-memory vs Hopfield-memory comparison outputs
- stronger real-chat Russian calibration for memory extraction
- report-quality debug traces and export artifacts
- learned Hopfield projections or differentiable `ksoftmax`
- general cleanup such as removing the FastAPI `on_event` deprecation path

### Current Trajectory

The project is no longer on a “build the missing core app” trajectory.

The live trajectory is now:

1. maintain the stable prototype
2. polish the student-facing documentation and thesis explanation
3. improve UX and answer quality where the payoff is obvious
4. only pursue extra artifact types or research comparisons if they materially help the thesis or demo

### Practical Interpretation

For the current repository, the most important roadmap fact is simple:

> The core product loop is already implemented. What remains is optional.
