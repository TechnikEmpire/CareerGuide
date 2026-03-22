# Project Status

Last updated: 2026-03-22

Последнее обновление: 2026-03-22

## English

### Current Phase

Foundational scaffold with repo governance, backend skeleton, bilingual documentation, and initial tests.

### What Is Already Done

- Bilingual authoritative repo documentation is in place.
- Canonical decision tracking is in place.
- Local setup instructions exist for WSL, Windows, and macOS.
- A Python-first backend scaffold exists with FastAPI routing and explicit service boundaries.
- The initial retrieval scaffold exists.
- The initial Hopfield-style associative-read scaffold exists.
- Bilingual evaluation scenarios exist.
- The first backend tests are passing in the `careerguide` Conda environment.

### What Is In Progress

- Moving from scaffold retrieval to real corpus-backed retrieval
- Aligning the production retrieval stack with Russian-first requirements
- Moving from stub generation to real `llama.cpp` integration
- Moving from placeholder evaluation to baseline-comparison evaluation

### What Is Not Done Yet

- Real authoritative corpus ingestion
- Normalized JSONL artifacts and corpus statistics
- SQLite-backed chunk and embedding index
- Production embedding and reranking stack
- Persistent memory storage
- Full safety policy implementation
- Full experiment harness and report-ready result exports

### Immediate Next Steps

1. Define and lock the first normalized corpus artifact shape.
2. Implement the first real ingestion pipeline, most likely O*NET.
3. Produce chunk artifacts and corpus statistics.
4. Replace scaffold retrieval inputs with corpus-backed multilingual retrieval.

### Current Risks and Notes

- The pinned generator model supports Russian. The production retrieval plan must therefore use multilingual retrieval components as well, rather than English-only embedding or reranking models.
- The current retrieval and generation behavior is still scaffold logic, not the final academic system.
- FastAPI currently raises a deprecation warning for `on_event`; this is not blocking, but it should be cleaned up when the app wiring matures.

### Latest Verification

- `python -m pytest backend/tests -q`
- Result: `5 passed`

## Русский

### Текущая фаза

Базовый scaffold с governance-документацией репозитория, skeleton backend, двуязычной документацией и первыми тестами.

### Что уже сделано

- Создана двуязычная authoritative-документация репозитория.
- Настроено каноническое отслеживание решений.
- Есть инструкции по локальной настройке для WSL, Windows и macOS.
- Существует Python-first backend scaffold с FastAPI-routing и явными границами сервисов.
- Существует начальный retrieval-scaffold.
- Существует начальный Hopfield-style associative-read scaffold.
- Существуют двуязычные evaluation-сценарии.
- Первые backend-тесты проходят в Conda-окружении `careerguide`.

### Что сейчас в работе

- Переход от scaffold-retrieval к реальному retrieval на основе корпуса
- Согласование production retrieval stack с требованием Russian-first
- Переход от stub-generation к реальной интеграции `llama.cpp`
- Переход от placeholder-evaluation к сравнению baseline-режимов

### Что еще не сделано

- Реальная загрузка авторитетного корпуса
- Нормализованные JSONL-артефакты и статистика корпуса
- SQLite-backed индекс chunk-ов и embeddings
- Production-стек для embeddings и reranking
- Persistent storage для памяти
- Полноценная реализация safety policy
- Полноценный experiment harness и экспорт результатов в report-ready формате

### Ближайшие шаги

1. Определить и зафиксировать форму первого нормализованного corpus-артефакта.
2. Реализовать первый настоящий ingestion pipeline, вероятнее всего для O*NET.
3. Сформировать chunk-артефакты и статистику корпуса.
4. Заменить scaffold-inputs retrieval на multilingual retrieval, работающий от реального корпуса.

### Текущие риски и заметки

- Зафиксированная модель-генератор поддерживает русский язык. Поэтому production retrieval plan тоже должен использовать multilingual-компоненты, а не English-only embedding или reranking модели.
- Текущее поведение retrieval и generation пока является scaffold-логикой, а не финальной академической системой.
- FastAPI сейчас выдает deprecation warning для `on_event`; это не блокирует работу, но должно быть приведено в порядок по мере взросления app wiring.

### Последняя проверка

- `python -m pytest backend/tests -q`
- Результат: `5 passed`
