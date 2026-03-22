# Active Decisions

Last updated: 2026-03-22

Последнее обновление: 2026-03-22

## D-001 Product Direction

**English**

- Status: active
- Decision: The product is a web-based career-guidance and work-life balance assistant.
- Rationale: This aligns with the repository identity and the student’s academic objective. Mobile and Android planning is out of scope for the active repository direction.

**Русский**

- Статус: активно
- Решение: Продукт является веб-ориентированным ассистентом по карьерному сопровождению и work-life balance.
- Обоснование: Это соответствует идентичности репозитория и академической цели студентки. Mobile и Android planning находятся вне активных границ репозитория.

## D-002 Primary Languages

**English**

- Status: active
- Decision: Use Python for backend and AI/data pipeline work. Use JavaScript or TypeScript for frontend work.
- Rationale: The student already knows Python and JavaScript, so the project should remain maximally understandable and maintainable.

**Русский**

- Статус: активно
- Решение: Использовать Python для backend и AI/data pipeline. Использовать JavaScript или TypeScript для frontend.
- Обоснование: Студентка уже знает Python и JavaScript, поэтому проект должен оставаться максимально понятным и сопровождаемым.

## D-003 Generator Runtime

**English**

- Status: active
- Decision: The default generator path is `Qwen2.5-1.5B-Instruct-GGUF` served via `llama.cpp`.
- Pinned artifact: `qwen2.5-1.5b-instruct-q4_k_m.gguf`
- Rationale: This path is compact, reproducible, practical for modest hardware, and aligned with the execution plan.

**Русский**

- Статус: активно
- Решение: Путь генератора по умолчанию - `Qwen2.5-1.5B-Instruct-GGUF`, обслуживаемый через `llama.cpp`.
- Зафиксированный артефакт: `qwen2.5-1.5b-instruct-q4_k_m.gguf`
- Обоснование: Этот путь компактен, воспроизводим, практичен для умеренного железа и согласован с execution plan.

## D-004 Retrieval Stack

**English**

- Status: active
- Decision: The MVP retrieval stack uses SQLite, SQLite FTS5, dense embeddings stored in tables, and reranking.
- Rationale: The corpus is expected to remain small enough for a transparent, lightweight MVP without introducing vector database complexity.

**Русский**

- Статус: активно
- Решение: В MVP retrieval stack использует SQLite, SQLite FTS5, dense embeddings, хранимые в таблицах, и reranking.
- Обоснование: Ожидается, что корпус останется достаточно небольшим для прозрачного и легковесного MVP без усложнения через vector database.

## D-005 User Language Priority

**English**

- Status: active
- Decision: The product is Russian-first for end users. English remains a supported language for collaboration, documentation, and review.
- Rationale: This matches the real audience and keeps implementation decisions aligned with the actual demo and thesis context.

**Русский**

- Статус: активно
- Решение: Продукт в первую очередь ориентирован на русскоязычных конечных пользователей. Английский язык остается поддерживаемым для совместной работы, документации и ревью.
- Обоснование: Это соответствует реальной аудитории проекта и не дает реализации отклониться от фактического demo- и thesis-контекста.

## D-006 Memory Novelty Framing

**English**

- Status: active
- Decision: The project uses a Hopfield-style associative memory layer as the main personalization novelty.
- Rationale: This connects the student’s recurrent-network background, especially LSTM-focused study, to a practical modern memory mechanism in a defensible way.
- Constraint: Documentation must describe this honestly as a practical associative-memory component, not as a claim that the project invented a new neural architecture or universally state-of-the-art system.

**Русский**

- Статус: активно
- Решение: Проект использует Hopfield-style associative memory layer как главный компонент новизны в персонализации.
- Обоснование: Это в защищаемой форме связывает бэкграунд студентки в recurrent networks, особенно обучение с акцентом на LSTM, с практическим современным memory mechanism.
- Ограничение: Документация должна описывать это честно как практический associative-memory компонент, а не как утверждение о создании новой нейросетевой архитектуры или универсально state-of-the-art системы.

## D-007 Evaluation Baseline

**English**

- Status: active
- Decision: The core experiment must compare `RAG-only` against `RAG + Hopfield-style memory`.
- Rationale: This is the cleanest way to test whether the memory layer produces measurable personalization value.

**Русский**

- Статус: активно
- Решение: Основной эксперимент должен сравнивать `RAG-only` и `RAG + Hopfield-style memory`.
- Обоснование: Это самый чистый способ проверить, дает ли memory layer измеримую ценность в персонализации.

## D-008 Documentation Policy

**English**

- Status: active
- Decision: Authoritative repository documentation must be bilingual in English and Russian.
- Rationale: The project should be understandable to both technical reviewers and the student across both languages without fragmenting the codebase itself.

**Русский**

- Статус: активно
- Решение: Авторитетная документация репозитория должна быть двуязычной: на английском и русском языках.
- Обоснование: Проект должен быть понятен как техническим проверяющим, так и студентке на обоих языках без раздробления самого кодового базиса.

## D-009 Bilingual Scenarios

**English**

- Status: active
- Decision: Evaluation scenarios and other enduring user-facing demo artifacts should include both English and Russian variants where practical.
- Rationale: The repository is bilingual by design, and the demo should show that the product concept can be exercised in both working languages.

**Русский**

- Статус: активно
- Решение: Evaluation-сценарии и другие долговечные user-facing demo-артефакты должны, где это практически возможно, включать варианты как на английском, так и на русском языках.
- Обоснование: Репозиторий изначально задуман как двуязычный, и демонстрация должна показывать, что концепция продукта может использоваться на обоих рабочих языках.

## D-010 Retrieval Models

**English**

- Status: active
- Decision: The planned production retrieval stack should use multilingual retrieval components: `BAAI/bge-m3` for embeddings and `BAAI/bge-reranker-v2-m3` for reranking.
- Rationale: The project is Russian-first, so production retrieval cannot depend on English-only components without introducing avoidable grounding errors.

**Русский**

- Статус: активно
- Решение: Планируемый production retrieval stack должен использовать multilingual-компоненты: `BAAI/bge-m3` для embeddings и `BAAI/bge-reranker-v2-m3` для reranking.
- Обоснование: Проект ориентирован прежде всего на русский язык, поэтому production retrieval не может опираться на English-only компоненты без лишних ошибок grounding.

## D-011 Progress Tracking

**English**

- Status: active
- Decision: Repository-native progress tracking should live in `docs/ROADMAP.md` and `docs/STATUS.md`.
- Rationale: This gives the project a durable, low-overhead planning and reporting mechanism without needing an external ticketing system.

**Русский**

- Статус: активно
- Решение: Внутреннее отслеживание прогресса проекта должно вестись в `docs/ROADMAP.md` и `docs/STATUS.md`.
- Обоснование: Это дает проекту устойчивый и малозатратный механизм планирования и отчетности без необходимости подключать внешнюю ticket-систему.

## Decision Maintenance Rule

**English**

When an active architectural, scope, stack, or evaluation decision changes, update this file in the same change.

**Русский**

Когда меняется активное архитектурное, scope-, stack- или evaluation-решение, обновляйте этот файл в том же изменении.
