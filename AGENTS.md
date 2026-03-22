# AGENTS.md

This file is the canonical operating guide for AI coding agents working in this repository.

Этот файл является каноническим руководством по работе для ИИ-агентов, которые вносят изменения в этот репозиторий.

## Authority Order

1. Active system and developer instructions from the execution environment
2. This file
3. `docs/PROJECT_CHARTER.md`
4. `docs/ENGINEERING_STANDARDS.md`
5. `docs/DECISIONS.md`
6. Current implementation plans in `plan/`

## Порядок приоритета

1. Активные системные и developer-инструкции из среды выполнения
2. Этот файл
3. `docs/PROJECT_CHARTER.md`
4. `docs/ENGINEERING_STANDARDS.md`
5. `docs/DECISIONS.md`
6. Актуальные планы реализации в `plan/`

## Mission

This repository exists to build an academic proof-of-concept web application for career guidance and work-life balance support. The system should demonstrate sound engineering, grounded retrieval, explainable personalization, and a practical research contribution that the student can defend clearly.

The student studies artificial intelligence and business. Her coursework has emphasized recurrent neural networks, especially LSTM. The Hopfield-style memory layer is included as the project’s practical novelty bridge between that background and a modern retrieval-augmented application.

## Миссия

Этот репозиторий существует для создания академического proof-of-concept веб-приложения по карьерному сопровождению и поддержке work-life balance. Система должна демонстрировать качественную инженерную реализацию, обоснованный retrieval, объяснимую персонализацию и практический исследовательский вклад, который студентка сможет уверенно защитить.

Студентка изучает искусственный интеллект и бизнес. В ее учебной программе был сильный акцент на рекуррентных сетях, особенно на LSTM. Hopfield-style memory layer включается в проект как практическая новизна, связывающая этот академический бэкграунд с современным retrieval-augmented приложением.

## Agent Rules

- Preserve the product scope: this is a web-based career guidance assistant, not an Android or mobile-first planner.
- Treat Russian as the primary end-user language. English support and English documentation exist for collaboration, review, and maintainability.
- Prefer Python for backend, ingestion, retrieval, memory, evaluation, and scripting.
- Prefer JavaScript or TypeScript for frontend work.
- Do not introduce other languages unless there is a concrete technical reason and the decision is recorded in `docs/DECISIONS.md`.
- Keep architecture explicit, modular, and inspectable. Favor simple modules and clear data flow over framework cleverness.
- Use self-documenting names first, then add explanatory comments generously around non-obvious logic, especially retrieval, memory, evaluation, data normalization, and prompt contracts.
- Avoid comments that only restate syntax.
- Keep enduring repository documentation bilingual in English and Russian.
- Keep source code identifiers in English. Keep most inline code comments in English for maintainability. If a short bilingual comment materially helps explain an academic concept, it is acceptable.
- When changing architecture, scope, model choices, or evaluation policy, update `docs/DECISIONS.md` in the same change.
- When material implementation progress happens, update `docs/STATUS.md`. When the stage map changes, update `docs/ROADMAP.md`.
- Do not overclaim the Hopfield-style memory layer. Describe it as a practical associative-memory mechanism and the project’s novelty component, but do not claim the project invented a new neural architecture.
- Prefer reproducibility over novelty theater. The student must be able to explain and demo the system clearly.

## Правила для агентов

- Сохраняйте границы продукта: это веб-ориентированный карьерный ассистент, а не Android- или mobile-first планировщик.
- Считайте русский язык основным языком конечного пользователя. Английская поддержка и английская документация существуют для совместной работы, ревью и сопровождаемости.
- Предпочитайте Python для backend, ingestion, retrieval, memory, evaluation и служебных скриптов.
- Предпочитайте JavaScript или TypeScript для frontend.
- Не вводите другие языки без конкретной технической необходимости и без фиксации решения в `docs/DECISIONS.md`.
- Архитектура должна быть явной, модульной и прозрачной для анализа. Предпочтение отдается простым модулям и понятному потоку данных, а не избыточной framework-сложности.
- Сначала используйте самодокументируемые имена, а затем щедро добавляйте поясняющие комментарии вокруг неочевидной логики, особенно в retrieval, memory, evaluation, нормализации данных и prompt-контрактах.
- Избегайте комментариев, которые просто пересказывают синтаксис.
- Вся долговечная документация репозитория должна поддерживаться на английском и русском языках.
- Идентификаторы в исходном коде должны быть на английском языке. Большинство inline-комментариев в коде также должны быть на английском ради сопровождаемости. Если короткий двуязычный комментарий действительно помогает объяснить академическую идею, это допустимо.
- При изменении архитектуры, границ проекта, выбора моделей или политики evaluation обновляйте `docs/DECISIONS.md` в том же изменении.
- При существенном изменении прогресса реализации обновляйте `docs/STATUS.md`. Если меняется карта стадий проекта, обновляйте `docs/ROADMAP.md`.
- Не делайте чрезмерных заявлений о Hopfield-style memory layer. Описывайте ее как практический associative-memory механизм и как компонент новизны проекта, но не утверждайте, что проект создает новую нейросетевую архитектуру.
- Предпочитайте воспроизводимость демонстративной новизне. Студентка должна уметь ясно объяснить и показать систему.

## Working Defaults

- Start with the simplest design that can still be defended academically.
- Prefer explicit schemas, deterministic scripts, and testable modules.
- Keep files focused. Split large modules before they become hard to read.
- When in doubt, optimize for student readability and thesis defensibility.

## Рабочие принципы по умолчанию

- Начинайте с наиболее простого решения, которое при этом можно академически защитить.
- Предпочитайте явные схемы, детерминированные скрипты и тестируемые модули.
- Держите файлы сфокусированными. Делите большие модули до того, как их станет трудно читать.
- При сомнениях оптимизируйте решение под понятность для студентки и защитимость в рамках выпускной работы.
