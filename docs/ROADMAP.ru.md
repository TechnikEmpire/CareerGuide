# Project Roadmap


Последнее обновление: 2026-04-28

### Назначение

Этот файл является картой стадий репозитория.

Он нужен, чтобы отвечать на вопросы:

- какие крупные фазы существуют
- какие из них уже завершены для текущего прототипа
- какие пункты теперь считаются optional polish, а не работой на критическом пути

Для более подробного описания текущего состояния используйте `docs/STATUS.md`.

### Легенда статусов

- `completed` = реализовано и принято в рамках текущего prototype-scope
- `optional` = явно отложено как polish, extension или более поздняя research-work

### Дорожная карта

| Stage | Status | Summary |
| --- | --- | --- |
| 0. Основа репозитория и governance | completed | Канонические правила репозитория, decisions tracking, setup-документация, engineering standards и governance реализации уже существуют. |
| 1. Сбор корпуса и нормализация | completed | Реализованы ingestion ESCO, normalization, bilingual translation и отслеживаемые preprocessing-артефакты. |
| 2. Эмбеддинги и retrieval index | completed | Репозиторий использует SQLite-persisted chunk data и FAISS HNSW retrieval artifacts с явными build-скриптами. |
| 3. Baseline RAG retrieval | completed | Dense-only retrieval измерен, пробенчмаркен и зафиксирован как активный baseline для текущего scope. |
| 4. LLM grounding и structured generation | completed | Реализованы grounded answer generation, explicit citations, structured plan generation и deterministic fallbacks. |
| 5. Persistent user memory | completed | Live-система сохраняет пользовательскую memory в SQLite и отдает ее через backend и frontend inspection-flow. |
| 6. Memory extraction и consolidation | completed | В live-path работают sentence-level binary BiLSTM extraction, preferred `pySBD` segmentation и normalized-text dedupe. |
| 7. Hopfield-style memory read | completed | Практический нетренируемый embedding-space Hopfield recall с режимами `top1` и `topk` подключен к live answer-path. |
| 8. Joint RAG + memory generation | completed | Live assistant уже объединяет dense retrieval, persisted memory и grounded conversational guardrails. |
| 9. Safety и scoped guidance behavior | completed | Прототип блокирует exploitative/out-of-scope requests, сохраняет unsupported plans grounded и дает limited caveated chat guidance для легитимных weakly grounded ролей. |
| 10. Evaluation baseline | completed | Для текущего prototype-scope уже существуют retrieval qrels, answer-eval fixtures, scoring scripts, benchmark outputs и ключевые regression tests. |
| 11. Web UI v1 | completed | Frontend уже покрывает chat, citations, memory, saved plans, study preferences, scheduled sessions, local history и `.ics`-экспорт. |
| 12. Deployment baseline | completed | Репозиторий теперь собирает, публикует и автоматически выкатывает single-image container, который раздает frontend и backend вместе и включает публичные local runtime models. |
| 13. Optional post-v1 refinement | optional | Все, что осталось, теперь является polish, research extension или thesis-strengthening work, а не отсутствующим product core. |

### Бэклог optional polish

Следующие пункты остаются полезными, но **не** блокируют текущий end-to-end
prototype:

- более сильный conversational polish и лучший стиль ответов
- более широкий safety-policy layer и более тонкое refusal coverage
- profile-level и artifact-level memory поверх текущей модели `memory_items`
- lifecycle-behavior для memory: confirm, archive, supersede
- дополнительные structured artifacts вроде `skills-gap` и `compare-options`
- отслеживаемые comparison-output для `RAG-only` vs naive-memory vs Hopfield-memory
- более сильная real-chat Russian calibration для memory extraction
- report-quality debug traces и export artifacts
- learned Hopfield projections или differentiable `ksoftmax`
- общий cleanup, например удаление FastAPI `on_event` deprecation path

### Текущая траектория

Проект больше не движется по траектории «достроить недостающий core app».

Текущая логика развития теперь такая:

1. поддерживать стабильный прототип
2. дополировать student-facing documentation и thesis explanation
3. улучшать UX и качество ответов там, где польза очевидна
4. возвращаться к дополнительным artifact types или research-comparisons только если это реально усиливает thesis или demo

### Практическая интерпретация

Для текущего репозитория самый важный факт roadmap звучит просто:

> Core product loop уже реализован. Все, что осталось, является optional.
