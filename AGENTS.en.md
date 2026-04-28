# AGENTS.md

This file is the English-language mirror of the canonical repository agent
guide in `AGENTS.md`.

## Authority Order

1. Active system and developer instructions from the execution environment
2. `AGENTS.md`
3. `docs/PROJECT_CHARTER.en.md`
4. `docs/ENGINEERING_STANDARDS.en.md`
5. `docs/DECISIONS.en.md`
6. Current implementation plans in `plan/`

## Mission

This repository exists to build an academic proof-of-concept web application
for career guidance and work-life balance support. The system should
demonstrate sound engineering, grounded retrieval, explainable
personalization, and a practical research contribution that the student can
defend clearly.

The student studies artificial intelligence and business. Her coursework has
emphasized recurrent neural networks, especially LSTM. The Hopfield-style
memory layer is included as the project’s practical novelty bridge between
that background and a modern retrieval-augmented application.

## Agent Rules

- Preserve the product scope: this is a web-based career guidance assistant,
  not an Android or mobile-first planner.
- Treat Russian as the primary end-user language. English support and English
  documentation exist for collaboration, review, and maintainability.
- Prefer Python for backend, ingestion, retrieval, memory, evaluation, and scripting.
- Prefer JavaScript or TypeScript for frontend work.
- Do not introduce other languages unless there is a concrete technical reason
  and the decision is recorded in `docs/DECISIONS.md`.
- Keep architecture explicit, modular, and inspectable. Favor simple modules
  and clear data flow over framework cleverness.
- Use self-documenting names first, then add explanatory comments generously
  around non-obvious logic, especially retrieval, memory, evaluation, data
  normalization, and prompt contracts.
- Avoid comments that only restate syntax.
- Before editing any Markdown file, check its last Git author with
  `git log -1 --format=%an -- <path>`. Do not edit Markdown files whose last
  author is `Junijus`; use another non-protected file or report that the
  translation/documentation update must be handled by that contributor.
- Keep enduring repository documentation in paired language-specific files
  where practical, using English and Russian variants such as `*.en.md` and
  `*.ru.md`.
- Keep source code identifiers in English. Keep most inline code comments in
  English for maintainability. If a short bilingual comment materially helps
  explain an academic concept, it is acceptable.
- When changing architecture, scope, model choices, or evaluation policy,
  update `docs/DECISIONS.md` in the same change.
- When material implementation progress happens, update `docs/STATUS.md`.
  When the stage map changes, update `docs/ROADMAP.md`.
- Do not overclaim the Hopfield-style memory layer. Describe it as a practical
  associative-memory mechanism and the project’s novelty component, but do not
  claim the project invented a new neural architecture.
- Prefer reproducibility over novelty theater. The student must be able to
  explain and demo the system clearly.

## Working Defaults

- Start with the simplest design that can still be defended academically.
- Prefer explicit schemas, deterministic scripts, and testable modules.
- Keep files focused. Split large modules before they become hard to read.
- When in doubt, optimize for student readability and thesis defensibility.
