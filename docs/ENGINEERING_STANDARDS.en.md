# Engineering Standards

### Primary Engineering Principles

- Prefer clarity over cleverness.
- Prefer explicit module boundaries over hidden coupling.
- Prefer simple, inspectable data flow over framework-heavy abstraction.
- Prefer correctness, traceability, and reproducibility over premature optimization.

### Code Structure

- Keep modules small and focused around one responsibility.
- Separate ingestion, retrieval, memory, generation, API, and evaluation concerns.
- Use clear function and variable names so the code reads like documentation.
- Avoid large monolithic scripts when reusable modules are more appropriate.
- Introduce shared utilities only after repeated, real duplication appears.

### Comments and Readability

- Use self-documenting code first.
- Be generous with comments where the logic is not obvious.
- Comments are especially encouraged for:
  - retrieval scoring and ranking logic
  - Hopfield-style memory read and write behavior
  - data normalization and schema mapping
  - prompt contracts and output schemas
  - evaluation logic and metrics
  - business rules that affect user-visible behavior
- Avoid trivial comments that only paraphrase code.
- Prefer English comments in source files. If a short bilingual comment helps explain an academic concept, it is acceptable.

### Python Standards

- Use Python for backend services, ingestion scripts, indexing, retrieval, evaluation, and orchestration by default.
- Favor typed function signatures and explicit data models.
- Prefer straightforward packages and modules over magic-heavy meta-programming.
- Keep side effects near the edges of the system.
- Write code that can be followed by a student who knows Python but may not know advanced framework internals.

### JavaScript and TypeScript Standards

- Use JavaScript or TypeScript for frontend work.
- Keep UI components small, readable, and composable.
- Keep client-side data flow explicit.
- Avoid introducing frontend complexity unless it clearly improves the demonstration.
- Add comments where UI state or data transformations are not obvious.

### Documentation Standards

- Durable repository documentation must exist in both English and Russian.
- Where practical, enduring docs should be maintained in paired language-specific files such as `*.en.md` and `*.ru.md`.
- The unsuffixed path may remain as a compatibility selector when stable links matter.
- When a change affects architecture, scope, stack, or research framing, update the relevant docs in the same change.
- `docs/DECISIONS.md` is the canonical place for active architectural and scope decisions.
- Plans in `plan/` may guide implementation, but they must not silently override the active decisions file.

### Testing and Verification

- Add tests or smoke checks for core logic whenever practical.
- Prioritize coverage for retrieval, memory selection, normalization, schemas, and evaluation logic.
- Verify behavior close to the changed module, not only through broad end-to-end checks.
- When evaluation fixtures or demo scenarios are user-facing, keep bilingual English and Russian coverage where practical.

### Repository Hygiene

- Keep filenames descriptive and stable.
- Prefer incremental, reviewable changes over large opaque rewrites.
- Do not add dependencies without a clear reason.
- If a dependency is added, document why it is needed.
