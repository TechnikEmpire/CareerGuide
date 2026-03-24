# CareerGuide

CareerGuide is an academic proof-of-concept web application for grounded
career guidance.

The current prototype already includes:

- grounded chat over the ESCO corpus
- sentence-level persistent memory
- Hopfield-style memory recall
- structured career plans
- schedule-aware plan sessions
- `.ics` calendar export
- a real web UI built on React + Vite

## Read This First

If you are the student or the main project operator, start here:

1. [Student Manual](docs/STUDENT_MANUAL.en.md)
2. [Setup Guide](docs/SETUP.en.md)
3. [Local Workflow](docs/LOCAL_WORKFLOW.en.md)
4. [Deployment Guide](docs/DEPLOYMENT.en.md)
5. [Project Status](docs/STATUS.en.md)
6. [Roadmap](docs/ROADMAP.en.md)

## Current Scope

Prototype v1 is complete for the current thesis/demo scope.

What remains is now optional polish or later research extension, not missing
core product behavior.

## Main System Surfaces

- Chat answer API: `POST /chat/answer`
- Career plan API: `POST /career/plan`
- Calendar export API: `POST /career/plan/export-ics`
- Memory listing API: `GET /memory/list`
- Memory delete API: `DELETE /memory/{memory_id}`
- Retrieval preview API: `POST /retrieval/preview`

## Main Folders

- `backend/` — FastAPI app, retrieval, memory, generation, scripts, tests
- `frontend/` — React + Vite web UI
- `data/` — raw and processed project data
- `models/` — local runtime model cache guidance
- `tooling/translation/` — ESCO normalization and translation tooling
- `tooling/memory_extraction/` — synthetic-data and BiLSTM memory tooling
- `docs/` — current source-of-truth documentation
- `plan/` — historical implementation planning docs

## Key Docs

- [Student Manual](docs/STUDENT_MANUAL.en.md)
- [Student Memory Guide](docs/STUDENT_MEMORY_GUIDE.en.md)
- [Project Charter](docs/PROJECT_CHARTER.en.md)
- [Engineering Standards](docs/ENGINEERING_STANDARDS.en.md)
- [Active Decisions](docs/DECISIONS.en.md)
- [Setup Guide](docs/SETUP.en.md)
- [Local Workflow](docs/LOCAL_WORKFLOW.en.md)
- [Deployment Guide](docs/DEPLOYMENT.en.md)
- [Evaluation](docs/EVALUATION.en.md)
- [Benchmarks](docs/BENCHMARKS.en.md)
- [Status](docs/STATUS.en.md)
- [Roadmap](docs/ROADMAP.en.md)

## Quick Start

Build retrieval artifacts:

```bash
python -m backend.scripts.build_retrieval_index
```

Start the local stack:

```bash
python -m backend.scripts.run_local_app_stack --reload
```

Start the frontend:

```bash
cd frontend
npm install
npm run dev
```

Build and run the single-image deployment container:

```bash
docker build -t careerguide:local .
docker run --rm -p 8000:8000 -v careerguide-data:/app/data/runtime careerguide:local
```

## Documentation Policy

Project-authored repository docs are now maintained in paired language-specific
files such as `*.en.md` and `*.ru.md`.

The unsuffixed path remains as a compatibility selector where that helps keep
stable links.

Third-party vendor docs, model cards, and installed dependency docs are not
rewritten by the project.
