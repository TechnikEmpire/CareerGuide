# План Codex: career-guidance web app с hybrid RAG и Hopfield-style memory

## Статус этого документа

Это **исторический рабочий план**, а не лучший источник ответа на вопрос
«что проект умеет прямо сейчас».

Для актуального состояния системы используйте:

- `docs/STUDENT_MANUAL.ru.md`
- `docs/STATUS.ru.md`
- `docs/ROADMAP.ru.md`
- `docs/DECISIONS.ru.md`

## Зачем этот документ вообще нужен

Этот план полезен как историческая запись того:

- как изначально формулировалась исследовательская цель
- почему в проекте появился Hopfield-style memory layer
- какие стадии ожидались в начале реализации
- какие научные и инженерные акценты считались главными

## Как его правильно читать сейчас

Читайте его как historical implementation background:

- для понимания исходного замысла
- для понимания более широкой research-framing
- для объяснения, почему проект не является просто «чатом поверх ESCO»

Не используйте его как канонический источник для:

- текущего списка реализованных features
- текущего UI-state
- актуального backlog
- текущих production-like behavior и runtime contracts

## Что изменилось относительно исходного плана

С момента написания этого плана проект дошел до более позднего состояния:

- dense-only retrieval стал активным baseline
- sentence-level memory extraction реально подключен к live backend
- persistent user memory и Hopfield recall уже работают
- web UI v1 уже завершен
- schedule-aware career plans и `.ics` export уже реализованы
- оставшаяся работа теперь относится в основном к optional polish и research-strengthening

## Практический вывод

Если вам нужен исторический контекст, этот документ полезен.

Если вам нужно понять живую систему, переходите в:

- `docs/STUDENT_MANUAL.ru.md`
- `docs/STATUS.ru.md`
- `docs/ROADMAP.ru.md`
