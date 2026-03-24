# План Codex: web-based career guidance assistant с dense ANN RAG и Hopfield-style memory

## Статус этого документа

Это **исторический webapp-план**, а не главный источник правды о текущем UI
или backend-состоянии.

Для актуального состояния используйте:

- `docs/STUDENT_MANUAL.ru.md`
- `docs/STATUS.ru.md`
- `docs/ROADMAP.ru.md`

## Для чего он все еще полезен

Документ остается полезным для понимания:

- исходной webapp-framing проекта
- ожидаемых product-surfaces
- research-positioning для grounded chat, memory и plans
- того, почему frontend задуман как thin client, а не как второй AI-layer

## Что уже реализовано сверх старого ожидания

Сейчас в репозитории уже есть:

- web UI v1
- grounded chat
- citations
- memory inspection и deletion
- local conversation history
- saved plan per profile
- schedule-aware plan preview
- `.ics` export
- refusal/scope UI states

## Что теперь считается optional

То, что раньше могло звучать как следующий обязательный шаг, теперь в основном
перешло в optional polish или future research-extension:

- дополнительные structured artifacts
- более богатый profile/artifact memory lifecycle
- более сильный evaluation harness для memory-comparison
- общий UX polish поверх уже работающего UI v1

## Практический вывод

Используйте этот документ как historical webapp background.

Для живой системы и текущей логики интерфейса переходите в:

- `docs/STUDENT_MANUAL.ru.md`
- `frontend/src/README.ru.md`
- `docs/STATUS.ru.md`
