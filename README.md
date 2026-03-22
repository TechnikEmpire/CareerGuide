# CareerGuide

Web-based personalized LLM for task oriented career development.

Веб-ориентированный персонализированный LLM для карьерного развития с практической направленностью.

Russian-first for end users. English documentation is maintained for collaboration and review.

Проект ориентирован в первую очередь на русскоязычных пользователей. Английская документация поддерживается для совместной работы и ревью.

## Authoritative Repository Docs

- `AGENTS.md` - canonical working guide for AI coding agents
- `docs/PROJECT_CHARTER.md` - project purpose, scope, and academic framing
- `docs/ENGINEERING_STANDARDS.md` - code quality, modularity, comments, and documentation rules
- `docs/DECISIONS.md` - active architectural and scope decisions
- `docs/SETUP.md` - local environment setup for WSL, Windows, and macOS
- `docs/ROADMAP.md` - long-horizon implementation stages
- `docs/STATUS.md` - current project snapshot and next steps

## Канонические документы репозитория

- `AGENTS.md` - основное рабочее руководство для ИИ-агентов
- `docs/PROJECT_CHARTER.md` - назначение проекта, границы и академическое позиционирование
- `docs/ENGINEERING_STANDARDS.md` - правила качества кода, модульности, комментариев и документации
- `docs/DECISIONS.md` - активные архитектурные и scope-решения
- `docs/SETUP.md` - настройка локального окружения для WSL, Windows и macOS
- `docs/ROADMAP.md` - долгосрочные стадии реализации
- `docs/STATUS.md` - текущий снимок проекта и ближайшие шаги

## Local Environment

Use the bilingual setup guide here:

- `docs/SETUP.md`

Default Conda environment name:

```text
careerguide
```

Quick test command:

```bash
python -m pytest backend/tests -q
```

## Локальное окружение

Используйте двуязычное руководство по настройке здесь:

- `docs/SETUP.md`

Имя Conda-окружения по умолчанию:

```text
careerguide
```

Быстрая команда для запуска тестов:

```bash
python -m pytest backend/tests -q
```

## Planning Docs

- `plan/codex_execution_plan_career_rag_hopfield.md`
- `plan/codex_plan_career_rag_hopfield_webapp.md`

## Примечание

Долговечная документация репозитория ведется на английском и русском языках. Код и идентификаторы в коде остаются на английском языке ради единообразия и сопровождаемости.
