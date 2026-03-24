# CareerGuide

CareerGuide — это академическое proof-of-concept веб-приложение для grounded
career guidance.

Текущий прототип уже включает:

- grounded chat поверх корпуса ESCO
- sentence-level persistent memory
- Hopfield-style memory recall
- structured career plans
- schedule-aware sessions внутри плана
- `.ics` calendar export
- реальный web UI на React + Vite

## Читать в первую очередь

Если вы студентка или основной оператор проекта, начинайте отсюда:

1. [Student Manual](docs/STUDENT_MANUAL.ru.md)
2. [Setup Guide](docs/SETUP.ru.md)
3. [Local Workflow](docs/LOCAL_WORKFLOW.ru.md)
4. [Deployment Guide](docs/DEPLOYMENT.ru.md)
5. [Project Status](docs/STATUS.ru.md)
6. [Roadmap](docs/ROADMAP.ru.md)

## Текущий scope

Prototype v1 завершен для текущего thesis/demo-scope.

Все, что осталось, теперь относится к optional polish или более поздним
research-extension, а не к отсутствующему core behavior продукта.

## Основные поверхности системы

- API ответа в чате: `POST /chat/answer`
- API карьерного плана: `POST /career/plan`
- API экспорта календаря: `POST /career/plan/export-ics`
- API списка памяти: `GET /memory/list`
- API удаления памяти: `DELETE /memory/{memory_id}`
- API preview retrieval: `POST /retrieval/preview`

## Основные папки

- `backend/` — FastAPI app, retrieval, memory, generation, scripts, tests
- `frontend/` — web UI на React + Vite
- `data/` — raw и processed project data
- `models/` — guidance по локальному runtime model cache
- `tooling/translation/` — tooling нормализации и перевода ESCO
- `tooling/memory_extraction/` — tooling synthetic-data и BiLSTM memory
- `docs/` — текущая source-of-truth документация
- `plan/` — исторические документы планирования реализации

## Ключевые документы

- [Student Manual](docs/STUDENT_MANUAL.ru.md)
- [Student Memory Guide](docs/STUDENT_MEMORY_GUIDE.ru.md)
- [Project Charter](docs/PROJECT_CHARTER.ru.md)
- [Engineering Standards](docs/ENGINEERING_STANDARDS.ru.md)
- [Active Decisions](docs/DECISIONS.ru.md)
- [Setup Guide](docs/SETUP.ru.md)
- [Local Workflow](docs/LOCAL_WORKFLOW.ru.md)
- [Deployment Guide](docs/DEPLOYMENT.ru.md)
- [Evaluation](docs/EVALUATION.ru.md)
- [Benchmarks](docs/BENCHMARKS.ru.md)
- [Status](docs/STATUS.ru.md)
- [Roadmap](docs/ROADMAP.ru.md)

## Быстрый старт

Соберите retrieval-артефакты:

```bash
python -m backend.scripts.build_retrieval_index
```

Запустите локальный стек:

```bash
python -m backend.scripts.run_local_app_stack --reload
```

Запустите frontend:

```bash
cd frontend
npm install
npm run dev
```

Соберите и запустите single-image deployment-container:

```bash
docker build -t careerguide:local .
docker run --rm -p 8000:8000 -v careerguide-data:/app/data/runtime careerguide:local
```

## Политика документации

Авторские документы репозитория теперь ведутся в парных language-specific
файлах вроде `*.en.md` и `*.ru.md`.

Путь без языкового суффикса остается compatibility-selector там, где это
помогает сохранить стабильные ссылки.

Документация third-party vendor, model cards и docs установленных зависимостей
проектом не переписываются.
