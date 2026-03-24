# Setup Guide

### Purpose

This guide explains how to create, activate, and verify the local Python environment for CareerGuide using Conda or Miniconda.

The default environment name used in this repository is:

```text
careerguide
```

### Prerequisites

- Conda, Miniconda, or Anaconda is installed
- Node.js 18+ and `npm` are installed for the web UI
- You can open a terminal in the repository root
- `requirements.txt` is present in the repository root

### WSL on Windows

Run these commands from the repository root:

```bash
cd /mnt/e/Work-Repos-SiftVPN/CareerGuide

source ~/miniconda3/etc/profile.d/conda.sh

conda create -n careerguide python=3.11 -y
conda activate careerguide

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If Miniconda is installed in a different location, replace:

```bash
source ~/miniconda3/etc/profile.d/conda.sh
```

with the correct path for your machine.

To activate the environment in later sessions:

```bash
cd /mnt/e/Work-Repos-SiftVPN/CareerGuide
source ~/miniconda3/etc/profile.d/conda.sh
conda activate careerguide
```

### Windows PowerShell

Open PowerShell after running `conda init powershell` once, or use Anaconda Prompt if Conda is not available in PowerShell yet.

```powershell
cd E:\Work-Repos-SiftVPN\CareerGuide

conda create -n careerguide python=3.11 -y
conda activate careerguide

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

To activate the environment in later sessions:

```powershell
cd E:\Work-Repos-SiftVPN\CareerGuide
conda activate careerguide
```

### Windows Command Prompt

If you prefer `cmd.exe`, open Anaconda Prompt or a Command Prompt where Conda has already been initialized.

```bat
cd /d E:\Work-Repos-SiftVPN\CareerGuide

conda create -n careerguide python=3.11 -y
conda activate careerguide

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

To activate the environment in later sessions:

```bat
cd /d E:\Work-Repos-SiftVPN\CareerGuide
conda activate careerguide
```

### macOS Terminal

If Conda is installed but shell activation is not loaded automatically, source Conda first.

```bash
cd /path/to/CareerGuide

source ~/miniconda3/etc/profile.d/conda.sh

conda create -n careerguide python=3.11 -y
conda activate careerguide

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

To activate the environment in later sessions:

```bash
cd /path/to/CareerGuide
source ~/miniconda3/etc/profile.d/conda.sh
conda activate careerguide
```

### Verification

After installation, verify the environment with:

```bash
python --version
python -m pip show faiss-cpu fastapi numpy pydantic sentence-transformers sqlalchemy transformers uvicorn
python -m pytest backend/tests -q
```

### Running Tests

With the environment active and the terminal opened at the repository root, run:

```bash
python -m pytest backend/tests -q
```

If you want more detailed output:

```bash
python -m pytest backend/tests -v
```

The smoke tests build a temporary deterministic retrieval index automatically,
so they do not require the real Qwen3 retrieval models or the persisted FAISS
artifacts.

### Setting Up The Frontend

The first web UI baseline now lives under `frontend/` and uses React + Vite.

Install the frontend dependencies from the repository root:

```bash
cd frontend
npm install
```

Verify the frontend bundle:

```bash
npm run build
```

Run the frontend development server:

```bash
npm run dev
```

Default frontend dev URL:

```text
http://127.0.0.1:5173
```

The frontend expects the FastAPI backend at:

```text
http://127.0.0.1:8000
```

If the backend runs on a different host or port, set:

```bash
export VITE_API_BASE_URL=http://HOST:PORT
```

before starting `npm run dev`.

### Building the Retrieval Index

Before running the real retrieval-backed backend, build the persisted ESCO
retrieval store and FAISS HNSW index explicitly:

```bash
python -m backend.scripts.build_retrieval_index
```

If you want to force a full rebuild:

```bash
python -m backend.scripts.build_retrieval_index --force
```

This command writes the persisted retrieval artifacts under:

- `data/processed/retrieval/faiss_hnsw.index`
- `data/processed/retrieval/faiss_hnsw_manifest.json`

Those files are now tracked by Git for the active Qwen3 retrieval
configuration.

If the tracked FAISS artifacts are already current but the local SQLite
retrieval rows are missing or stale, the same command restores the SQLite rows
without a full corpus re-embedding pass.

### Setting Up Local Runtime Models

The canonical local setup helper now downloads the required runtime models into
repo-local directories, creates `.env.local`, and writes the local generation
server config automatically.

Run:

```bash
python -m backend.scripts.setup_local_models
```

What this does:

- downloads the generator GGUF into `models/Qwen3-0.6B-GGUF/`
- downloads the retrieval embedding model into `models/Qwen3-Embedding-0.6B/`
- writes `.env.local` so the backend uses the repo-local embedding model
- writes `config/llama_cpp_python_server.local.json` with the resolved GGUF path

The backend now loads `.env.local` automatically, so you do not need to export
the local embedding path manually after running the setup helper.

The retrieval index and manifest now use a stable logical model ID for
`Qwen/Qwen3-Embedding-0.6B`, so switching the runtime from the Hugging Face repo
ID to the repo-local model directory does not by itself invalidate the tracked
retrieval artifacts.

Because the local embedding model is now repo-local, the canonical local
generation and answer-export workflow should not need to hit Hugging Face at
runtime unless you explicitly choose an online path.

### Running the Local App Stack

The backend now expects an OpenAI-compatible local generation server for real
generation. The preferred local implementation is the Python package
`llama-cpp-python[server]`.

Install the optional runtime package in your existing environment:

```bash
python -m pip install -r requirements-runtime.txt
```

This package may still compile native `llama.cpp` components during
installation, or install a prebuilt wheel if one is available. That is expected.

Default base URL:

```text
http://127.0.0.1:8080
```

After `python -m backend.scripts.setup_local_models`, the default app command is:

```bash
python -m backend.scripts.run_local_app_stack --reload
```

This starts:

1. the local GGUF generation server
2. the FastAPI backend app

If the generation server is already running, the stack command reuses it and
starts only the backend app process.

If you want to control those processes manually instead of using the single
stack command, the advanced commands are:

```bash
python -m backend.scripts.run_local_generation_server
python -m backend.scripts.run_backend_dev_server --reload
```

If your generator runs elsewhere, set:

```bash
export CAREERGUIDE_GENERATION_BASE_URL=http://HOST:PORT
```

### Running Canonical Retrieval Benchmarks

The canonical retrieval benchmark command is:

```bash
python -m backend.scripts.benchmark_retrieval
```

If you want dense retrieval on CPU:

```bash
python -m backend.scripts.benchmark_retrieval --mode dense
```

If you also want the heavier diagnostic full-context benchmark path:

```bash
python -m backend.scripts.benchmark_retrieval --mode full --hf-home /tmp/careerguide_hf_cache
```

CPU-only is the default benchmark behavior. Use `--allow-gpu` only if you
explicitly want CUDA for the heavier model-backed modes.

The active runtime baseline is dense-only retrieval. The full benchmark mode is
kept for diagnostic comparison, not because reranking is part of the default
path.

The current dense-only runtime default is `top_k=10`. While reranking remains
disabled, `candidate_pool` is not an active runtime lever.

The benchmark command does not rebuild retrieval artifacts. If it reports stale
artifacts, run `python -m backend.scripts.build_retrieval_index` first.

The benchmark query set is tracked in:

- `eval/retrieval_benchmark_queries.json`

Full interpretation rules are documented in:

- `docs/BENCHMARKS.md`

### Scoring Canonical Evaluation Outputs

The tracked evaluation fixtures live in:

- `eval/retrieval_qrels.json`
- `eval/answer_eval_cases.json`

To score retrieval predictions against the canonical qrels:

```bash
python -m backend.scripts.export_retrieval_predictions --output-json eval/out/retrieval_predictions_dense.json
python -m eval.score_eval --retrieval-predictions eval/out/retrieval_predictions_dense.json
```

To score cited-evidence overlap for answer cases:

```bash
python -m eval.score_eval --answer-predictions /path/to/answer_predictions.json
```

This answer-evidence score is only canonical when `answer_predictions.json`
contains model-selected `cited_chunk_ids`. Older exports that treated the
entire retrieved context as if it were the cited set should be regenerated
before comparison.

### Running the Canonical Local Evaluation Workflow

To run the current dense-only local evaluation workflow end to end, use:

```bash
python -m backend.scripts.run_local_eval_workflow
```

This wrapper does three things:

1. writes `eval/out/dense_retrieval_tuning.json`
2. writes `eval/out/answer_predictions.json`
3. writes `eval/out/answer_scores.json`

It is the easiest way to reproduce the current local answer-evaluation stage
without manually invoking three separate commands.

Before it starts generation, the wrapper also validates the persisted retrieval
artifacts and refreshes them automatically if the local SQLite rows or FAISS
metadata are stale.

The wrapper now inherits the active runtime defaults, including `top_k=10`.
It also depends on the current explicit-citation export path, so rerun it after
changes to answer citation parsing or generation formatting.

If the local generation server is already running, the wrapper reuses it.

To persist the canonical dense and reranker retrieval-eval state:

```bash
python -m backend.scripts.export_retrieval_predictions --output-json eval/out/retrieval_predictions_dense.json
python -m eval.score_eval --retrieval-predictions eval/out/retrieval_predictions_dense.json --output-json eval/out/retrieval_scores_dense.json

python -m backend.scripts.export_retrieval_predictions --use-reranker --output-json eval/out/retrieval_predictions_rerank.json
python -m eval.score_eval --retrieval-predictions eval/out/retrieval_predictions_rerank.json --output-json eval/out/retrieval_scores_rerank.json
```

Current interpretation of the tracked score reports:

- dense is the active baseline
- reranking is currently not recommended for runtime use
- the reranker outputs are retained as a scored negative ablation result

Canonical dense-only tuning run:

```bash
python -m backend.scripts.tune_dense_retrieval --output-json eval/out/dense_retrieval_tuning.json
```

Canonical answer-generation export and score:

```bash
python -m backend.scripts.export_answer_predictions --output-json eval/out/answer_predictions.json
python -m eval.score_eval --answer-predictions eval/out/answer_predictions.json --output-json eval/out/answer_scores.json
```

### Running the Backend

Once the environment is active, start the backend with:

```bash
uvicorn backend.app.main:app --reload
```

If the retrieval artifacts are missing or stale, the backend will now tell you
to run the retrieval build command instead of silently rebuilding them on the
first query.

### One-Time ESCO Translation Tooling

The ESCO preprocessing and translation workflow uses a standalone tooling module
with separate requirements:

- `tooling/translation/requirements.txt`

Recommended installation flow in a separate Conda environment:

```bash
conda create -n careerguide-tools python=3.11 -y
conda activate careerguide-tools

python -m pip install --upgrade pip
python -m pip install -r tooling/translation/requirements.txt
```

Typical preprocessing commands:

```bash
python -m tooling.translation.normalize_esco_csv
python -m tooling.translation.translate_esco_to_russian
```

Current recommended full-run command for an RTX 4090 workstation:

```bash
python -m tooling.translation.translate_esco_to_russian \
  --text-batch-size 64 \
  --record-batch-size 8 \
  --num-beams 1 \
  --max-source-length 256 \
  --max-new-tokens 256
```

Important notes:

- ESCO concept URIs are the stable identifiers that let the project join bilingual concept text back to the ESCO relation graph.
- The current ESCO English CSV dump contains a small number of duplicate concept rows that differ only by `modifiedDate`.
- The normalizer collapses duplicate concept rows by URI and keeps the latest source row.
- The translation script resumes automatically when `--overwrite` is not used.

The detailed process is documented in:

- `docs/ESCO_PREPROCESSING.md`

### Standalone Memory-Extraction Tooling

The bilingual sentence-classification workflow for memory extraction now also
uses a standalone tooling module with separate requirements:

- `tooling/memory_extraction/requirements.txt`
- `tooling/memory_extraction/README.md`

Recommended installation flow in the same standalone Conda environment:

```bash
conda activate careerguide-tools
python -m pip install -r tooling/memory_extraction/requirements.txt
```

Canonical workflow:

```bash
python -m tooling.memory_extraction.generate_synthetic_dataset --model-source Qwen/Qwen3-0.6B --device cuda
python -m tooling.memory_extraction.prepare_dataset --task binary
python -m tooling.memory_extraction.train_bilstm_classifier --task binary
python -m tooling.memory_extraction.evaluate_classifier --task binary
```

Important notes:

- v1 targets only `ru` and `en`
- the classifier is a lightweight BiLSTM; the standalone binary baseline is now trained, evaluated, and wired into the current live backend memory-write path
- the raw synthetic corpus keeps fine-grained labels, but the first supervised extractor baseline is binary `MEMORY` vs `NO_MEMORY`
- synthetic corpus generation loads the chosen model directly inside the tooling process and is intended to use the workstation GPU
- the live backend now prefers `pySBD` sentence splitting in the `careerguide` app environment and falls back to regex segmentation if `pysbd` is not yet installed there
- after pulling these changes, refresh the main `careerguide` environment from `requirements.txt` so the preferred splitter is available at runtime
- generated corpora and trained model bundles under `tooling/memory_extraction/` may be persisted in git when you want the dataset, checkpoint, and reports tracked for reproducibility
- the currently tracked supervised artifacts are the `memory_extraction_synthetic_v4` corpus plus the binary BiLSTM bundles and reports under `tooling/memory_extraction/models/`
