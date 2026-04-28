# Local Workflow


Последнее обновление: 2026-03-23

### Для чего нужен этот workflow

Этот документ простыми словами объясняет текущий локальный workflow разработки.

Для single-image deployment-path используйте [docs/DEPLOYMENT.ru.md](DEPLOYMENT.ru.md).

На текущей стадии проекта есть четыре разных типа работы:

1. one-time preprocessing корпуса
2. one-time или редкая сборка retrieval-index
3. повторяемая локальная evaluation и runtime-валидация генерации ответов
4. повторяемая разработка web UI поверх стабильных backend-контрактов

Это разные этапы. Это не одно и то же.

### Что уже сделано

Следующие тяжелые шаги уже завершены и зафиксированы в Git:

- нормализация ESCO
- перевод ESCO с английского на русский
- сборка retrieval-index на базе FAISS HNSW
- evaluation dense-versus-reranker для retrieval

Это означает, что проект уже не находится в режиме подготовки корпуса.

### Что проект делает сейчас

Активный baseline теперь такой:

1. использовать отслеживаемые ESCO-артефакты
2. использовать отслеживаемый retrieval-index на базе FAISS HNSW
3. эмбеддить только входящий query
4. извлекать dense ANN chunks
5. собирать grounded prompt
6. запрашивать ответ у локального Qwen3.5 GGUF generator
7. score-ить сгенерированный ответ по отслеживаемым answer-eval cases

Активный dense-only runtime-default теперь — `top_k=10`, исходя из текущей
отслеживаемой tuning-кривой.

### Почему локальные модели все еще нужны

Даже если retrieval-index уже собран, генерация ответов все равно требует:

- локальный runtime генератора для `bartowski/Qwen_Qwen3.5-2B-GGUF:Q4_K_M`
- локальную embedding-модель для query-эмбеддинга (`Qwen/Qwen3-Embedding-0.6B`)

Retrieval-index хранит document-векторы, но система все равно должна эмбеддить
каждый входящий query до того, как сможет искать по индексу.

Repo-local setup-helper записывает `.env.local`, и backend автоматически
загружает этот файл. Именно так локальный путь к query-embedding-модели
активируется без ручного shell-export.

### Что делает текущий web UI

Первый baseline UI теперь существует в `frontend/`.

На текущем этапе он поддерживает:

- выбор профиля через поле user-id
- grounded-chat через `POST /chat/answer`
- явное отображение citations
- явное отображение “memory used” из answer-response
- structured plan generation через `POST /career/plan`
- просмотр memory через `GET /memory/list`

UI намеренно остается тонким. Он напрямую обращается к FastAPI-backend и не
вводит второй frontend-side AI-runtime layer.

### Канонические локальные команды

One-time setup локальных моделей:

```bash
python -m backend.scripts.setup_local_models
```

Запуск полного локального app-stack одной командой:

```bash
python -m backend.scripts.run_local_app_stack --reload
```

Этот startup-path теперь проверяет retrieval-артефакты перед запуском backend
server и автоматически восстанавливает их, если отслеживаемый FAISS-cache или
SQLite retrieval-rows устарели.

Если вы хотите вручную управлять двумя процессами, используйте advanced-команды:

```bash
python -m backend.scripts.run_local_generation_server
python -m backend.scripts.run_backend_dev_server --reload
```

Запуск канонического локального evaluation-workflow:

```bash
python -m backend.scripts.run_local_eval_workflow
```

Если локальный generation-server уже работает, evaluation-wrapper повторно
использует его вместо запуска дублирующего процесса.
Если persisted retrieval-артефакты устарели, wrapper обновит их до старта
generation.

Запуск frontend против локального backend:

```bash
cd frontend
npm install
npm run dev
```

Frontend dev URL по умолчанию — `http://127.0.0.1:5173`. Backend теперь
разрешает локальные CORS-запросы от `127.0.0.1` и `localhost` на портах `5173`
и `3000`.

Если backend не работает на `http://127.0.0.1:8000`, задайте
`VITE_API_BASE_URL` перед запуском frontend.

### Канонические Hopfield-тесты для запуска

Целевые unit- и smoke-level тесты для текущего Hopfield-memory slice:

```bash
python -m pytest backend/tests/test_hopfield_memory.py -q
python -m pytest backend/tests/test_memory_store.py -q
python -m pytest backend/tests/test_app.py -q
python -m pytest backend/tests/test_dev_server_scripts.py -q
```

Эти автоматизированные тесты покрывают Hopfield recall helpers, app-level
memory-path и сборку reload-команды без необходимости поднимать несколько
консолей.

Ручной smoke для live-app по режимам:

```bash
CAREERGUIDE_MEMORY_HOPFIELD_MODE=top1 python -m backend.scripts.run_local_app_stack --reload
CAREERGUIDE_MEMORY_HOPFIELD_MODE=topk CAREERGUIDE_MEMORY_HOPFIELD_TOP_K=3 python -m backend.scripts.run_local_app_stack --reload
```

После этого стоит сделать несколько повторных запросов к `/chat/answer` для
одного и того же пользователя, затем проверить `/memory/list` и убедиться, что
prompt-path повторно использует persisted memory в обоих режимах recall.

### Что производит evaluation-workflow

Локальный evaluation-workflow записывает три канонических output-файла:

- `eval/out/dense_retrieval_tuning.json`
- `eval/out/answer_predictions.json`
- `eval/out/answer_scores.json`

Они отвечают на три разных вопроса:

- `dense_retrieval_tuning.json`
  - Какой выбор dense-only top-k сейчас лучше всего score-ится на отслеживаемых qrels?
- `answer_predictions.json`
  - Какие ответы и какие явные citation-ID chunk-ов выдал текущий retrieval-plus-generation stack?
- `answer_scores.json`
  - Насколько эти сгенерированные ответы пересекаются с ожидаемыми evidence chunks?

Score для answer-evidence теперь зависит от model-selected `cited_chunk_ids`, а
не от полного списка retrieved-context. Любые старые answer-output, созданные
до этого исправления citation-path, считаются устаревшими и должны быть
перегенерированы.
Следующее обновление должно уже провалидировать новый default `top_k=10`,
более жесткие generation prompt/runtime-настройки и сам explicit citation-path.

### Чего мы сейчас не делаем

Текущий workflow не:

- пересобирает translated ESCO layer
- пересобирает FAISS index при каждом запуске; retrieval-артефакты обновляются только когда они устарели
- использует reranker в активном path

Reranker уже был протестирован и сохранен только как отрицательный ablation-result.
