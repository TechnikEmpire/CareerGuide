# Setup Guide

## English

### Purpose

This guide explains how to create, activate, and verify the local Python environment for CareerGuide using Conda or Miniconda.

The default environment name used in this repository is:

```text
careerguide
```

### Prerequisites

- Conda, Miniconda, or Anaconda is installed
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

## Русский

### Назначение

Это руководство объясняет, как создать, активировать и проверить локальное Python-окружение для CareerGuide с помощью Conda или Miniconda.

Имя окружения по умолчанию в этом репозитории:

```text
careerguide
```

### Предварительные требования

- установлен Conda, Miniconda или Anaconda
- вы можете открыть терминал в корне репозитория
- в корне репозитория присутствует `requirements.txt`

### WSL в Windows

Запустите эти команды из корня репозитория:

```bash
cd /mnt/e/Work-Repos-SiftVPN/CareerGuide

source ~/miniconda3/etc/profile.d/conda.sh

conda create -n careerguide python=3.11 -y
conda activate careerguide

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Если Miniconda установлена в другом месте, замените:

```bash
source ~/miniconda3/etc/profile.d/conda.sh
```

на корректный путь для вашей машины.

Чтобы активировать окружение в следующих сессиях:

```bash
cd /mnt/e/Work-Repos-SiftVPN/CareerGuide
source ~/miniconda3/etc/profile.d/conda.sh
conda activate careerguide
```

### Windows PowerShell

Откройте PowerShell после однократного выполнения `conda init powershell` или используйте Anaconda Prompt, если Conda пока недоступна в PowerShell.

```powershell
cd E:\Work-Repos-SiftVPN\CareerGuide

conda create -n careerguide python=3.11 -y
conda activate careerguide

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Чтобы активировать окружение в следующих сессиях:

```powershell
cd E:\Work-Repos-SiftVPN\CareerGuide
conda activate careerguide
```

### Windows Command Prompt

Если вы предпочитаете `cmd.exe`, откройте Anaconda Prompt или Command Prompt, где Conda уже была инициализирована.

```bat
cd /d E:\Work-Repos-SiftVPN\CareerGuide

conda create -n careerguide python=3.11 -y
conda activate careerguide

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Чтобы активировать окружение в следующих сессиях:

```bat
cd /d E:\Work-Repos-SiftVPN\CareerGuide
conda activate careerguide
```

### macOS Terminal

Если Conda установлена, но активация оболочки не подключается автоматически, сначала подключите Conda вручную.

```bash
cd /path/to/CareerGuide

source ~/miniconda3/etc/profile.d/conda.sh

conda create -n careerguide python=3.11 -y
conda activate careerguide

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Чтобы активировать окружение в следующих сессиях:

```bash
cd /path/to/CareerGuide
source ~/miniconda3/etc/profile.d/conda.sh
conda activate careerguide
```

### Проверка

После установки проверьте окружение командами:

```bash
python --version
python -m pip show faiss-cpu fastapi numpy pydantic sentence-transformers sqlalchemy transformers uvicorn
python -m pytest backend/tests -q
```

### Запуск тестов

При активированном окружении и открытом терминале в корне репозитория выполните:

```bash
python -m pytest backend/tests -q
```

Если нужен более подробный вывод:

```bash
python -m pytest backend/tests -v
```

Smoke-тесты автоматически собирают временный deterministic retrieval-index, поэтому
им не нужны реальные retrieval-модели Qwen3 и сохраненные FAISS-артефакты.

### Сборка Retrieval-Index

Перед запуском реального retrieval-backed backend необходимо явно собрать
persisted ESCO retrieval store и FAISS HNSW index:

```bash
python -m backend.scripts.build_retrieval_index
```

Если нужна принудительная полная пересборка:

```bash
python -m backend.scripts.build_retrieval_index --force
```

Эта команда записывает persisted retrieval-артефакты в:

- `data/processed/retrieval/faiss_hnsw.index`
- `data/processed/retrieval/faiss_hnsw_manifest.json`

Эти файлы теперь отслеживаются Git для активной конфигурации retrieval на
Qwen3.

Если отслеживаемые FAISS-артефакты уже актуальны, а локальные SQLite
retrieval-rows отсутствуют или устарели, та же команда восстановит SQLite-rows
без полного повторного прохода эмбеддинга по корпусу.

### Настройка локальных runtime-моделей

Канонический local setup-helper теперь автоматически скачивает необходимые
runtime-модели в локальные каталоги репозитория, создает `.env.local` и пишет
локальную конфигурацию generation-server.

Запустите:

```bash
python -m backend.scripts.setup_local_models
```

Что делает эта команда:

- скачивает generator GGUF в `models/Qwen3-0.6B-GGUF/`
- скачивает retrieval embedding-модель в `models/Qwen3-Embedding-0.6B/`
- пишет `.env.local`, чтобы backend использовал локальную embedding-модель
- пишет `config/llama_cpp_python_server.local.json` с уже разрешенным GGUF-path

Backend теперь автоматически загружает `.env.local`, поэтому после запуска
setup-helper не нужно вручную export-ить локальный embedding-path.

Retrieval-index и manifest теперь используют стабильный логический model ID для
`Qwen/Qwen3-Embedding-0.6B`, поэтому переход от Hugging Face repo ID к
repo-local каталогу модели сам по себе не делает отслеживаемые
retrieval-артефакты устаревшими.

Поскольку локальная embedding-модель теперь лежит в репозитории, канонический
локальный generation- и answer-export workflow не должен обращаться к Hugging
Face во время runtime, если только вы явно не выбираете online-путь.

### Запуск локального app-stack

Теперь backend ожидает локальный OpenAI-compatible generation-server для
реальной generation. Предпочтительная локальная реализация - Python-пакет
`llama-cpp-python[server]`.

Установите optional runtime-пакет в уже существующее окружение:

```bash
python -m pip install -r requirements-runtime.txt
```

Этот пакет все равно может компилировать нативные компоненты `llama.cpp` во
время установки или установить готовый wheel, если он доступен. Это ожидаемое
поведение.

Базовый URL по умолчанию:

```text
http://127.0.0.1:8080
```

После `python -m backend.scripts.setup_local_models` командой по умолчанию для
app является:

```bash
python -m backend.scripts.run_local_app_stack --reload
```

Эта команда запускает:

1. локальный GGUF generation-server
2. FastAPI backend app

Если generation-server уже работает, команда stack повторно использует его и
запускает только backend app process.

Если вы хотите вручную управлять этими двумя процессами вместо единой команды
stack, advanced-команды такие:

```bash
python -m backend.scripts.run_local_generation_server
python -m backend.scripts.run_backend_dev_server --reload
```

Если генератор работает в другом месте, установите:

```bash
export CAREERGUIDE_GENERATION_BASE_URL=http://HOST:PORT
```

### Запуск канонических retrieval-benchmark

Каноническая команда benchmark для retrieval:

```bash
python -m backend.scripts.benchmark_retrieval
```

Если нужен benchmark dense retrieval на CPU:

```bash
python -m backend.scripts.benchmark_retrieval --mode dense
```

Если нужен более тяжелый diagnostic-benchmark для full-context:

```bash
python -m backend.scripts.benchmark_retrieval --mode full --hf-home /tmp/careerguide_hf_cache
```

CPU-only теперь является поведением benchmark по умолчанию. Используйте
`--allow-gpu` только если вы явно хотите CUDA для более тяжелых model-backed
режимов.

Активный runtime-baseline использует dense-only retrieval. Полный benchmark
режим сохранен для диагностического сравнения, а не потому, что reranking
входит в path по умолчанию.

Текущий dense-only runtime-default — `top_k=10`. Пока reranking выключен,
`candidate_pool` не является активным runtime-рычагом.

Команда benchmark не пересобирает retrieval-артефакты. Если она сообщает, что
артефакты устарели, сначала выполните
`python -m backend.scripts.build_retrieval_index`.

Набор benchmark-запросов отслеживается в:

- `eval/retrieval_benchmark_queries.json`

Полные правила интерпретации описаны в:

- `docs/BENCHMARKS.md`

### Scoring канонических evaluation-output

Отслеживаемые evaluation-fixtures находятся в:

- `eval/retrieval_qrels.json`
- `eval/answer_eval_cases.json`

Чтобы оценить retrieval-predictions по каноническим qrels:

```bash
python -m backend.scripts.export_retrieval_predictions --output-json eval/out/retrieval_predictions_dense.json
python -m eval.score_eval --retrieval-predictions eval/out/retrieval_predictions_dense.json
```

Чтобы оценить overlap cited-evidence для answer-cases:

```bash
python -m eval.score_eval --answer-predictions /path/to/answer_predictions.json
```

Этот score для answer-evidence считается каноническим только тогда, когда
`answer_predictions.json` содержит model-selected `cited_chunk_ids`. Старые
export-файлы, которые считали цитатами весь retrieved-context, нужно
перегенерировать перед сравнением.

Чтобы зафиксировать каноническое persisted-состояние dense и reranker
retrieval-eval:

```bash
python -m backend.scripts.export_retrieval_predictions --output-json eval/out/retrieval_predictions_dense.json
python -m eval.score_eval --retrieval-predictions eval/out/retrieval_predictions_dense.json --output-json eval/out/retrieval_scores_dense.json

python -m backend.scripts.export_retrieval_predictions --use-reranker --output-json eval/out/retrieval_predictions_rerank.json
python -m eval.score_eval --retrieval-predictions eval/out/retrieval_predictions_rerank.json --output-json eval/out/retrieval_scores_rerank.json
```

Текущая интерпретация отслеживаемых score-report:

- dense является активным baseline
- reranking сейчас не рекомендуется для runtime-использования
- output reranker сохраняются как scored отрицательный ablation-result

Канонический запуск dense-only tuning:

```bash
python -m backend.scripts.tune_dense_retrieval --output-json eval/out/dense_retrieval_tuning.json
```

Канонический экспорт и score answer-generation:

```bash
python -m backend.scripts.export_answer_predictions --output-json eval/out/answer_predictions.json
python -m eval.score_eval --answer-predictions eval/out/answer_predictions.json --output-json eval/out/answer_scores.json
```

### Запуск канонического локального evaluation-workflow

Чтобы выполнить текущий dense-only local evaluation-workflow целиком,
используйте:

```bash
python -m backend.scripts.run_local_eval_workflow
```

Этот wrapper делает три вещи:

1. записывает `eval/out/dense_retrieval_tuning.json`
2. записывает `eval/out/answer_predictions.json`
3. записывает `eval/out/answer_scores.json`

Это самый простой способ воспроизвести текущую стадию локальной
answer-evaluation без ручного запуска трех отдельных команд.

Перед запуском generation wrapper также проверяет persisted
retrieval-артефакты и автоматически обновляет их, если локальные SQLite-rows
или FAISS-metadata устарели.

Wrapper теперь наследует активные runtime-default, включая `top_k=10`.
Он также зависит от текущего explicit-citation export-path, поэтому его нужно
перезапускать после изменений в parsing цитат или формате generation-output.

Если локальный generation-server уже работает, wrapper повторно использует его.

### Запуск backend

После активации окружения backend можно запустить так:

```bash
uvicorn backend.app.main:app --reload
```

Если retrieval-артефакты отсутствуют или устарели, backend теперь явно скажет
запустить команду сборки retrieval-index вместо того, чтобы молча пересобирать
их при первом запросе.

### One-Time ESCO Translation Tooling

Для preprocessing и translation workflow ESCO используется standalone tooling-модуль
с отдельными зависимостями:

- `tooling/translation/requirements.txt`

Рекомендуемый способ установки в отдельное Conda-окружение:

```bash
conda create -n careerguide-tools python=3.11 -y
conda activate careerguide-tools

python -m pip install --upgrade pip
python -m pip install -r tooling/translation/requirements.txt
```

Типичные команды preprocessing:

```bash
python -m tooling.translation.normalize_esco_csv
python -m tooling.translation.translate_esco_to_russian
```

Текущая рекомендуемая full-run команда для workstation с RTX 4090:

```bash
python -m tooling.translation.translate_esco_to_russian \
  --text-batch-size 64 \
  --record-batch-size 8 \
  --num-beams 1 \
  --max-source-length 256 \
  --max-new-tokens 256
```

Важные замечания:

- ESCO concept URI являются стабильными идентификаторами, которые позволяют проекту связывать bilingual concept text обратно с ESCO relation graph.
- Текущий English CSV dump ESCO содержит небольшое число duplicate concept rows, которые отличаются только `modifiedDate`.
- Normalizer схлопывает duplicate concept rows по URI и сохраняет самую новую source row.
- Translation script автоматически возобновляет работу, если не использовать `--overwrite`.

Подробный процесс описан в:

- `docs/ESCO_PREPROCESSING.md`

### Standalone tooling для memory extraction

Workflow двуязычной sentence-classification для memory extraction теперь тоже
использует отдельный standalone tooling-модуль со своими requirements:

- `tooling/memory_extraction/requirements.txt`
- `tooling/memory_extraction/README.md`

Рекомендуемый install-flow в том же standalone Conda-окружении:

```bash
conda activate careerguide-tools
python -m pip install -r tooling/memory_extraction/requirements.txt
```

Канонический workflow:

```bash
python -m tooling.memory_extraction.generate_synthetic_dataset --model-source Qwen/Qwen3-0.6B --device cuda
python -m tooling.memory_extraction.prepare_dataset --task binary
python -m tooling.memory_extraction.train_bilstm_classifier --task binary
python -m tooling.memory_extraction.evaluate_classifier --task binary
```

Важные замечания:

- генерация synthetic corpus напрямую загружает выбранную модель внутри tooling-процесса и рассчитана на использование workstation GPU
- v1 нацелен только на `ru` и `en`
- classifier является легким BiLSTM; standalone binary baseline уже обучен, оценен и подключен к текущему live backend memory write-path
- raw synthetic corpus сохраняет fine-grained labels, но первый supervised extractor baseline является бинарным: `MEMORY` vs `NO_MEMORY`
- live-backend теперь предпочитает sentence-splitting через `pySBD` в app-env `careerguide` и откатывается к regex-segmentation, если `pysbd` там еще не установлен
- после получения этих изменений обновите основное окружение `careerguide` из `requirements.txt`, чтобы preferred splitter был доступен в runtime
- generated corpora и trained model-bundles в `tooling/memory_extraction/` могут сохраняться в git, если вам нужна воспроизводимость dataset, checkpoint и reports
- текущие отслеживаемые supervised-артефакты — это corpus `memory_extraction_synthetic_v4` и binary BiLSTM bundles/reports в `tooling/memory_extraction/models/`
