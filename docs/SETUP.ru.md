# Setup Guide

### Назначение

Это руководство объясняет, как создать, активировать и проверить локальное Python-окружение для CareerGuide с помощью Conda или Miniconda.

Имя окружения по умолчанию в этом репозитории:

```text
careerguide
```

### Предварительные требования

- установлен Conda, Miniconda или Anaconda
- для web UI установлен Node.js 18+ и `npm`
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

### Настройка Frontend

Первый baseline web UI теперь находится в `frontend/` и использует React +
Vite.

Установите frontend-зависимости из корня репозитория:

```bash
cd frontend
npm install
```

Проверьте, что frontend-бандл собирается:

```bash
npm run build
```

Запустите frontend dev-server:

```bash
npm run dev
```

URL frontend по умолчанию:

```text
http://127.0.0.1:5173
```

Frontend по умолчанию ожидает FastAPI-backend по адресу:

```text
http://127.0.0.1:8000
```

Если backend работает на другом host или port, задайте:

```bash
export VITE_API_BASE_URL=http://HOST:PORT
```

перед запуском `npm run dev`.

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
