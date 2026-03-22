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
python -m backend.scripts.export_retrieval_predictions --output-json eval/out/retrieval_predictions.json
python -m eval.score_eval --retrieval-predictions eval/out/retrieval_predictions.json
```

To score cited-evidence overlap for answer cases:

```bash
python -m eval.score_eval --answer-predictions /path/to/answer_predictions.json
```

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
python -m backend.scripts.export_retrieval_predictions --output-json eval/out/retrieval_predictions.json
python -m eval.score_eval --retrieval-predictions eval/out/retrieval_predictions.json
```

Чтобы оценить overlap cited-evidence для answer-cases:

```bash
python -m eval.score_eval --answer-predictions /path/to/answer_predictions.json
```

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
