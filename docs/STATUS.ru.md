# Project Status


Последнее обновление: 2026-03-26

### Текущая фаза

Проект сейчас находится в состоянии **Prototype v1 complete** в рамках
текущего академического демонстрационного scope.

Это означает, что в репозитории уже есть:

- рабочий FastAPI-backend
- рабочий web UI на React + Vite
- grounded retrieval по обработанным ESCO-артефактам
- локальная model-based генерация ответов
- sentence-level memory extraction через отслеживаемый binary BiLSTM bundle
- persistent memory storage и Hopfield-style memory recall
- structured career plans с schedule metadata и `.ics`-экспортом
- single deployment-image, который раздает SPA и backend вместе
- автоматический SSH-based rollout из GitHub Actions на production Linode host

Оставшаяся работа больше не является «отсутствующей core-функциональностью
продукта». Теперь это optional polish, research-extension work или более
поздняя thesis-improvement work.

### Что прототип уже умеет

- Отдает реальный backend API из `backend/app/`.
- Строит dense retrieval по отслеживаемому ESCO-corpus на базе SQLite + FAISS HNSW.
- Использует `Qwen/Qwen3-Embedding-0.6B` как активный retrieval embedder.
- Использует локальный OpenAI-compatible generation server для `Qwen/Qwen3-0.6B`.
- Возвращает grounded chat-ответы с citations.
- Хранит sentence-level user memory в SQLite-таблице `memory_items`.
- Извлекает memory через отслеживаемый binary BiLSTM classifier bundle.
- Разбивает user turns на sentence-like segments с `pySBD` как preferred path и regex как fallback.
- Дедуплицирует memory по normalized text на пользователя.
- Вызывает memory через нетренируемый Hopfield-style read в embedding-space с режимами `top1` и `topk`.
- Отказывает в неподдерживаемых или явно out-of-scope запросах вместо того, чтобы выдумывать ответы.
- Генерирует structured career plans с study-preferences, workload metadata и датированными calendar sessions.
- Экспортирует сохраненные планы в `.ics`.
- Содержит реальный frontend для chat, plan generation, local conversation history, memory inspection, memory deletion и UI-подачи refusal/scope states.
- Раздает собранный frontend прямо из backend в single-image deployment-path.
- Собирает и публикует deployable container-image через GitHub Actions после успешного CI на `main`.
- Автоматически выкатывает production Linode-host после успешной публикации image на `main`.

### Что проверено

- Backend-тесты покрывают retrieval, generation contracts, memory extraction,
  memory storage, Hopfield recall, plan scheduling, refusal behavior и API-routes.
- Frontend успешно собирается через Vite.
- Retrieval-артефакты, evaluation fixtures и scored evaluation outputs уже есть
  в репозитории.
- Schedule-aware plan-artifact и `.ics`-экспорт реализованы и покрыты тестами.
- Single-image SPA-serving path в backend покрыт app-тестами, а deployment-конфигурация зафиксирована в репозитории.

### Канонические точки входа

Для понимания текущей live-системы начинайте с:

- `README.md`
- `docs/STUDENT_MANUAL.ru.md`
- `docs/ROADMAP.md`
- `docs/DECISIONS.md`
- `docs/LOCAL_WORKFLOW.md`
- `docs/SETUP.md`
- `docs/DEPLOYMENT.md`

### Что осталось

Все пункты ниже теперь являются **optional polish**, **research extension** или
**post-v1 refinement**. Ни один из них не нужен, чтобы считать текущий
прототип функционально завершенным.

- Улучшение conversational style и prompt polish
- Более широкий safety-policy layer поверх текущего grounded refusal
- Более богатый lifecycle memory: confirm, archive, supersede
- Profile-level и artifact-level memory поверх текущего среза `memory_items`
- Дополнительные structured artifacts вроде `skills-gap` или `compare-options`, если они останутся в scope
- Отслеживаемые comparison-output для `RAG-only` vs naive-memory vs Hopfield-memory в исследовательской части
- Более сильная real-chat Russian calibration для memory extraction
- Report-quality debug exports и comparison traces
- Cleanup-долг вроде deprecation warning для FastAPI `on_event`
### Практический смысл слова «готово»

Для первой thesis/demo-версии «готово» теперь означает:

1. студентка может локально запустить приложение
2. студентка может объяснить flow retrieval + memory + plan
3. UI демонстрирует задуманные product surfaces
4. оставшийся backlog явно зафиксирован как optional refinement

Это условие теперь выполнено.

### Текущие риски и честные оговорки

- Ассистент уже функционален, но местами все еще стилистически шероховат,
  потому что generator маленький, а corpus сильно ESCO-centric.
- Live memory extractor значительно реальнее старой heuristic-версии, но его
  главные доказательства все еще опираются на synthetic data и targeted runtime
  tests, а не на большой real-chat benchmark.
- Текущий Hopfield-layer — это практический associative-memory mechanism поверх
  реальных embedding-векторов, а не финальная learned differentiable phase из
  более широкой research-framing.
- В репозитории есть исторические plan-документы, чьи детальные checkpoint-ы
  местами старше текущей реализации. В качестве актуального источника правды
  используйте student manual, roadmap и этот status-файл.

### Последний проверенный срез

- Retrieval stack: SQLite + FAISS HNSW + `Qwen/Qwen3-Embedding-0.6B`
- Generator stack: локальный OpenAI-compatible server + `Qwen/Qwen3-0.6B`
- Memory store: SQLite `memory_items`
- Memory extraction: sentence-level binary BiLSTM runtime-path
- Memory recall: Hopfield-style `top1` и `topk`
- Plan artifact: structured steps + schedule metadata + calendar events + `.ics`-экспорт
- Frontend stack: React + Vite + TypeScript
- Deployment baseline: один Docker-image, same-origin SPA + backend, GHCR publish + Linode rollout через GitHub Actions
- Frontend surfaces: chat, citations, memory-used display, saved plan, preview календаря, список/удаление memory, local history
- Prototype status: завершен для текущего v1-scope
