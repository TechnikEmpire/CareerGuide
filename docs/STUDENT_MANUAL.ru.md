# Руководство для студентки

Последнее обновление: 2026-03-24

## 1. Что это за проект

CareerGuide — это академическое proof-of-concept веб-приложение для grounded
career guidance. Это не general-purpose chatbot, не mobile-planner и не просто
UI для document search.

Система должна:

- отвечать на карьерные вопросы, опираясь на grounded ESCO evidence
- запоминать устойчивые пользовательские предпочтения из диалога
- позже вызывать эти memories через Hopfield-style механизм
- генерировать structured career plans
- превращать планы в schedule-aware study sessions и `.ics`-экспорт

Если нужен один тезис для защиты, используйте такую формулировку:

> CareerGuide объединяет dense retrieval, grounded generation и практический
> Hopfield-style memory layer для персонализации карьерных рекомендаций, не
> утверждая, что проект изобрел новую нейросетевую архитектуру.

## 2. Что уже закончено

Для текущего prototype-scope система уже достаточно завершена для demo и
защиты.

Готовые core-features:

- grounded chat-ответы
- citations
- sentence-level memory extraction
- persistent memory storage
- Hopfield-style memory recall
- structured career plans
- schedule-aware calendar sessions
- `.ics`-экспорт
- web UI с chat, plan, history и memory views
- refusal behavior для unsupported и out-of-scope requests

Чего уже **не** не хватает:

- frontend
- persistence для memory
- plan generation
- calendar export
- live backend integration

Все, что осталось, теперь относится к optional polish, а не к отсутствующему
core behavior продукта.

## 3. В каком порядке читать документы

Чтобы быстро разобраться в проекте, используйте такой порядок:

1. `README.ru.md`
   Зачем: быстрое знакомство с репозиторием
2. [`docs/STUDENT_MANUAL.ru.md`](./STUDENT_MANUAL.ru.md)
   Зачем: этот документ объясняет всю систему по feature-группам
3. [`docs/STUDENT_MEMORY_GUIDE.ru.md`](./STUDENT_MEMORY_GUIDE.ru.md)
   Зачем: memory-subsystem — самая сильная академическая зона владения студентки
4. [`docs/SETUP.ru.md`](./SETUP.ru.md)
   Зачем: окружение и локальная настройка
5. [`docs/LOCAL_WORKFLOW.ru.md`](./LOCAL_WORKFLOW.ru.md)
   Зачем: как реально запускать стек и evaluation scripts
6. [`docs/STATUS.ru.md`](./STATUS.ru.md)
   Зачем: что завершено, а что optional
7. [`docs/ROADMAP.ru.md`](./ROADMAP.ru.md)
   Зачем: карта стадий и что отложено
8. [`docs/DECISIONS.ru.md`](./DECISIONS.ru.md)
   Зачем: почему архитектура выглядит именно так

Длинные plan-документы в `plan/` используйте только как исторический контекст
реализации. Это уже не лучший источник ответа на вопрос «что репозиторий умеет
сейчас».

## 4. Карта репозитория

Это основные папки, которые нужно понимать.

### `backend/`

Это реальный backend приложения.

Важные подпапки:

- `backend/app/api/` — FastAPI-routes
- `backend/app/services/retrieval/` — логика retrieval
- `backend/app/services/memory/` — extraction, persistence и recall памяти
- `backend/app/services/generation/` — prompt building, generator client, планы
- `backend/scripts/` — operator scripts
- `backend/tests/` — regression tests

### `frontend/`

Это web UI.

Важные файлы:

- `frontend/src/App.tsx` — главный shell приложения и page-level state
- `frontend/src/api/client.ts` — HTTP-клиент к backend
- `frontend/src/components/` — message cards, citations, memory panel
- `frontend/src/styles.css` — текущая visual-system и layout

### `data/`

Здесь находятся project data.

- `data/raw/ESCO/` — raw ESCO source dumps
- `data/processed/esco/` — normalized и bilingual ESCO artifacts
- `data/processed/retrieval/` — retrieval-артефакты FAISS
- `data/processed/careerguide.db` — SQLite app database

### `tooling/translation/`

One-time preprocessing и translation tooling для ESCO.

### `tooling/memory_extraction/`

Standalone tooling для synthetic memory data generation, classifier training и
classifier evaluation.

### `docs/`

Текущая source-of-truth документация.

### `plan/`

Исторические рабочие планы. Полезны как background, но не как первое место для
поиска актуального состояния реализации.

## 5. Основные user-facing features

Этот раздел объясняет приложение по feature-группам, а не по файлам.

### 5.1 Chat

Пользователь вводит вопрос во frontend. Приложение отправляет его в:

- `POST /chat/answer`

Далее backend:

1. проверяет, находится ли запрос в допустимом scope
2. staging-ом извлекает memory-candidates из user message
3. строит retrieval-context из ESCO
4. вызывает релевантную сохраненную память
5. собирает grounded prompt
6. либо возвращает deterministic guardrailed answer, либо вызывает локальную модель
7. сохраняет staged memory только если запрос был выполнен и не был отклонен

Основные файлы:

- [`backend/app/api/assistant.py`](../backend/app/api/assistant.py)
- [`backend/app/services/assistant_service.py`](../backend/app/services/assistant_service.py)
- [`backend/app/services/retrieval/rag_pipeline.py`](../backend/app/services/retrieval/rag_pipeline.py)
- [`backend/app/services/generation/prompt_builder.py`](../backend/app/services/generation/prompt_builder.py)
- [`backend/app/services/generation/generator_client.py`](../backend/app/services/generation/generator_client.py)
- [`backend/app/services/generation/answer_guardrails.py`](../backend/app/services/generation/answer_guardrails.py)

### 5.2 Citations

Каждый ответ может показывать retrieved chunks, на которых он основан.

Это важно, потому что проект должен быть академически защищаемым. Студентка
должна уметь объяснить:

- какие evidence были retrieved
- какие evidence реально были процитированы
- почему ответ можно считать grounded

Основные файлы:

- [`backend/app/services/generation/schemas.py`](../backend/app/services/generation/schemas.py)
- [`backend/app/services/retrieval/rag_pipeline.py`](../backend/app/services/retrieval/rag_pipeline.py)
- [`frontend/src/components/CitationList.tsx`](../frontend/src/components/CitationList.tsx)

### 5.3 Memory

Memory здесь не является свободной магией.

Текущая система делает следующее:

1. разбивает user turn на sentence-like segments
2. классифицирует каждый segment как `MEMORY` или `NO_MEMORY`
3. оставляет только принятые сегменты
4. дедуплицирует их по normalized text
5. сохраняет их в SQLite
6. позже вызывает наиболее релевантные memory items через Hopfield-style read

Важная деталь:

- отклоненные запросы **не** сохраняют новую память

Основные файлы:

- [`backend/app/services/memory/sentence_split.py`](../backend/app/services/memory/sentence_split.py)
- [`backend/app/services/memory/runtime_classifier.py`](../backend/app/services/memory/runtime_classifier.py)
- [`backend/app/services/memory/memory_extract.py`](../backend/app/services/memory/memory_extract.py)
- [`backend/app/services/memory/memory_consolidate.py`](../backend/app/services/memory/memory_consolidate.py)
- [`backend/app/services/memory/memory_store.py`](../backend/app/services/memory/memory_store.py)
- [`backend/app/services/memory/hopfield_memory.py`](../backend/app/services/memory/hopfield_memory.py)

### 5.4 Plans

Фича плана — это не просто «длинный ответ».

Она использует:

- plan request
- retrieved ESCO evidence
- study preferences
- deterministic schedule generation

Backend возвращает:

- target role
- workload level
- estimated weeks
- ordered steps
- calendar events
- citations

Основные файлы:

- [`backend/app/services/generation/plan_guardrails.py`](../backend/app/services/generation/plan_guardrails.py)
- [`backend/app/services/generation/plan_calendar.py`](../backend/app/services/generation/plan_calendar.py)
- [`backend/app/services/generation/esco_grounding.py`](../backend/app/services/generation/esco_grounding.py)
- [`backend/app/services/generation/schemas.py`](../backend/app/services/generation/schemas.py)

### 5.5 Calendar Export

Сохраненные планы можно экспортировать как `.ics`.

Этот path намеренно backend-owned. Frontend не придумывает собственную
scheduling-логику.

Основные файлы:

- [`backend/app/api/assistant.py`](../backend/app/api/assistant.py)
- [`backend/app/services/generation/plan_calendar.py`](../backend/app/services/generation/plan_calendar.py)
- [`frontend/src/api/client.ts`](../frontend/src/api/client.ts)

### 5.6 Conversation History

История разговоров сейчас хранится локально во frontend, а не как server-side
multi-user infrastructure.

Frontend теперь создает opaque browser-local profile code и отправляет этот
код как backend `user_id`. Copy/import доступен для осознанной миграции, но
это не real account system.

Frontend хранит:

- conversations для каждого local profile code
- один saved plan на local profile code
- один theme choice на local profile code

Это намеренно сделано простым.

Основной файл:

- [`frontend/src/App.tsx`](../frontend/src/App.tsx)

### 5.7 Просмотр и удаление memory

В UI есть memory-view, чтобы студентка могла посмотреть, что именно ассистент
запомнил.

Пользователь может:

- получить список memory items
- удалить отдельную memory item

Основные файлы:

- [`backend/app/api/memory.py`](../backend/app/api/memory.py)
- [`frontend/src/components/MemoryPanel.tsx`](../frontend/src/components/MemoryPanel.tsx)
- [`frontend/src/api/client.ts`](../frontend/src/api/client.ts)

### 5.8 Refusal и scope handling

Ассистент не должен радостно выдумывать guidance для unsupported,
exploitative или явно out-of-scope requests.

Текущее поведение:

- блокировать unsupported role/planning requests
- блокировать exploitative или illegal work requests
- возвращать спокойные scope/refusal messages в UI

Основные файлы:

- [`backend/app/services/safety/safety.py`](../backend/app/services/safety/safety.py)
- [`backend/app/services/generation/answer_guardrails.py`](../backend/app/services/generation/answer_guardrails.py)
- [`backend/app/services/assistant_service.py`](../backend/app/services/assistant_service.py)

## 6. End-to-end flow по feature-группам

### 6.1 Flow ответа

Используйте это описание, когда объясняете chat-path на защите или demo.

1. Frontend отправляет запрос из [`frontend/src/api/client.ts`](../frontend/src/api/client.ts).
2. FastAPI принимает его в [`backend/app/api/assistant.py`](../backend/app/api/assistant.py).
3. `assistant_service.answer_question()` orchestrates весь запрос.
4. Из вопроса staging-ом извлекаются memory-candidates.
5. В [`backend/app/services/retrieval/rag_pipeline.py`](../backend/app/services/retrieval/rag_pipeline.py) строится retrieval-context.
6. В [`backend/app/services/memory/hopfield_memory.py`](../backend/app/services/memory/hopfield_memory.py) строится summary памяти.
7. В [`backend/app/services/generation/prompt_builder.py`](../backend/app/services/generation/prompt_builder.py) собирается prompt.
8. Guardrails могут сразу вернуть deterministic answer.
9. Иначе generator client обращается к локальному model server.
10. Response нормализуется к общей schema.
11. Если answer был успешно выполнен, staged memory сохраняется.
12. Frontend показывает answer, citations и summary использованной памяти.

### 6.2 Flow плана

1. Frontend отправляет `goal`, `target_role` и `study_preferences`.
2. FastAPI принимает запрос на `POST /career/plan`.
3. `assistant_service.build_career_plan()` выполняет retrieval и support-checks.
4. Prompt собирается с grounded ESCO-context.
5. Generator возвращает structured plan-content, либо используется deterministic fallback.
6. Schedule enrichment превращает план в датированные sessions.
7. Frontend показывает steps, schedule и citations.
8. Frontend может запросить `.ics`-экспорт для saved plan.

### 6.3 Flow записи memory

1. Пользователь отправляет сообщение.
2. Runtime-splitter создает sentence-like segments.
3. BiLSTM-classifier оценивает каждый segment.
4. Positive memory-candidates помещаются в staging.
5. Они preview-ятся для текущего turn.
6. Если answer отклонен, ничего нового не сохраняется.
7. Если answer успешен, candidates upsert-ятся в `memory_items`.

Это правило «stage before commit» важно и его стоит упоминать, если вас
спросят, как система избегает обучения на отклоненных запросах.

## 7. API-surface

Это самые важные routes.

### `POST /chat/answer`

Главный conversational endpoint.

Request:

- `user_id` (browser-local profile code)
- `question`

Response:

- `answer`
- `citations`
- `prompt_preview`
- `memory_summary`
- `response_kind`

### `POST /career/plan`

Endpoint для structured plan.

Request:

- `user_id` (browser-local profile code)
- `goal`
- `target_role`
- `study_preferences`

Response:

- role и workload metadata
- ordered plan steps
- calendar events
- citations

### `POST /career/plan/export-ics`

Принимает payload сохраненного плана и возвращает скачиваемый calendar file.

### `GET /memory/list`

Возвращает persisted memory для одного пользователя.

### `DELETE /memory/{memory_id}`

Удаляет один memory item для одного пользователя.

### `POST /retrieval/preview`

Debug/inspection-route, который показывает ranked retrieved chunks.

### `POST /eval/run-scenarios`

Этот endpoint пока существует только как placeholder/stub и не является
основным evaluation-path сегодня.

## 8. Data и model artifacts

### ESCO source layer

Текущий проект grounded главным образом на ESCO.

Важные артефакты:

- `data/processed/esco/normalized/esco_concepts.en.jsonl`
- `data/processed/esco/normalized/esco_relations.jsonl`
- `data/processed/esco/bilingual/esco_concepts.en_ru.jsonl`

### Retrieval artifacts

- `data/processed/retrieval/faiss_hnsw.index`
- `data/processed/retrieval/faiss_hnsw_manifest.json`

### App database

- `data/processed/careerguide.db`

Здесь хранятся:

- rows памяти
- retrieval-side SQLite state, который использует backend

### Local model artifacts

Смотрите [`models/README.ru.md`](../models/README.ru.md).

Важные runtime-models:

- generator: `Qwen/Qwen3.5-2B` Q4_K_M GGUF
- embedder: `Qwen/Qwen3-Embedding-0.6B`
- memory classifier bundle: [`tooling/memory_extraction/models/bilstm_memory_classifier_binary.pt`](../tooling/memory_extraction/models/bilstm_memory_classifier_binary.pt)

## 9. Tooling, которое нужно понимать

### Translation tooling

Находится в [`tooling/translation/`](../tooling/translation/README.md).

Назначение:

- нормализация raw ESCO CSV data
- перевод concept-layer ESCO на русский
- выпуск отслеживаемых bilingual artifacts

### Memory extraction tooling

Находится в [`tooling/memory_extraction/`](../tooling/memory_extraction/README.md).

Назначение:

- генерация synthetic sentence-level memory data
- подготовка binary splits
- обучение BiLSTM-classifier
- оценка classifier

Важный момент:

Это tooling отделено от live backend runtime, хотя обученный bundle затем и
используется backend.

## 10. Как запускать проект

Используйте полные инструкции в [`docs/SETUP.ru.md`](./SETUP.ru.md) и
[`docs/LOCAL_WORKFLOW.ru.md`](./LOCAL_WORKFLOW.ru.md).

Самое короткое summary:

1. активировать conda-env `careerguide`
2. при необходимости собрать retrieval-artifacts
3. запустить локальный backend/generator stack
4. запустить frontend

Основные команды:

```bash
python -m backend.scripts.build_retrieval_index
python -m backend.scripts.run_local_app_stack --reload
```

Затем в другом терминале:

```bash
cd frontend
npm install
npm run dev
```

## 11. Как тестировать проект

Вам не нужно помнить каждый тест.

Наиболее полезные группы:

- [`backend/tests/test_app.py`](../backend/tests/test_app.py) — поведение API
- [`backend/tests/test_memory_extract.py`](../backend/tests/test_memory_extract.py) — runtime-поведение memory extraction
- [`backend/tests/test_memory_store.py`](../backend/tests/test_memory_store.py) — persistent memory behavior
- [`backend/tests/test_hopfield_memory.py`](../backend/tests/test_hopfield_memory.py) — поведение recall
- [`backend/tests/test_plan_calendar.py`](../backend/tests/test_plan_calendar.py) — schedule generation и calendar logic
- [`backend/tests/test_answer_guardrails.py`](../backend/tests/test_answer_guardrails.py) — refusal и grounded overrides

Для frontend наиболее прямой check по-прежнему такой:

```bash
cd frontend
npm run build
```

## 12. Как академически объяснять архитектуру

Используйте такое объяснение:

- Система — это grounded career-guidance assistant.
- Retrieval реализован как dense ANN поверх обработанных ESCO data.
- Generation выполняется маленькой локальной моделью за OpenAI-compatible API.
- Memory явно хранится как persistent user facts/preferences в SQLite.
- Memory recall выполняется через практический Hopfield-style associative step поверх реальных embedding-vectors.
- Web UI намеренно тонкий и напрямую вызывает backend.

Важное правило честности:

**Не** утверждайте, что текущий repo уже реализует финальную learned
differentiable Hopfield-phase. Это не так. Сейчас реализована практическая
associative-memory phase.

## 13. Что осталось как optional polish

Эти пункты реальны, но optional:

- более плавный стиль answer-output
- более широкий safety-policy layer
- более богатые lifecycle-controls для memory
- больше structured artifact types
- более сильные research comparison-output для memory ablations
- более сильная real-chat Russian calibration
- report-oriented debug exports

Если кто-то спросит: «Что осталось?», правильный ответ такой:

> Core system уже готов. Остались polish и более сильные research-grade evidence.

## 14. Куда смотреть, если что-то ломается

### Если ломается retrieval

Смотрите:

- [`backend/app/services/retrieval/faiss_hnsw.py`](../backend/app/services/retrieval/faiss_hnsw.py)
- [`backend/scripts/build_retrieval_index.py`](../backend/scripts/build_retrieval_index.py)
- [`data/processed/retrieval/`](../data/processed/retrieval/README.md)

### Если ломается local model server

Смотрите:

- [`backend/app/services/generation/generator_client.py`](../backend/app/services/generation/generator_client.py)
- [`backend/app/config.py`](../backend/app/config.py)
- [`backend/scripts/run_local_generation_server.py`](../backend/scripts/run_local_generation_server.py)

### Если странно ведет себя memory

Смотрите:

- [`backend/app/services/memory/memory_extract.py`](../backend/app/services/memory/memory_extract.py)
- [`backend/app/services/memory/runtime_classifier.py`](../backend/app/services/memory/runtime_classifier.py)
- [`backend/app/services/memory/memory_store.py`](../backend/app/services/memory/memory_store.py)
- [`backend/app/services/memory/hopfield_memory.py`](../backend/app/services/memory/hopfield_memory.py)

### Если странно выглядят планы

Смотрите:

- [`backend/app/services/generation/plan_guardrails.py`](../backend/app/services/generation/plan_guardrails.py)
- [`backend/app/services/generation/plan_calendar.py`](../backend/app/services/generation/plan_calendar.py)
- [`backend/app/services/generation/esco_grounding.py`](../backend/app/services/generation/esco_grounding.py)

### Если странно выглядит UI

Смотрите:

- [`frontend/src/App.tsx`](../frontend/src/App.tsx)
- [`frontend/src/styles.css`](../frontend/src/styles.css)
- [`frontend/src/components/`](../frontend/src/README.md)

## 15. Последний совет студентке

Если вы чувствуете, что потерялись, не начинайте со всех файлов сразу.

Начните с:

1. этого manual
2. [`frontend/src/App.tsx`](../frontend/src/App.tsx)
3. [`backend/app/services/assistant_service.py`](../backend/app/services/assistant_service.py)
4. [`backend/app/services/retrieval/rag_pipeline.py`](../backend/app/services/retrieval/rag_pipeline.py)
5. [`backend/app/services/memory/`](../backend/app/services/memory/)
6. [`backend/app/services/generation/`](../backend/app/services/generation/)

Этот путь даст вам самое быстрое и реальное понимание того, как работает
приложение.
