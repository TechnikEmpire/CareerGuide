# Engineering Standards

## English

### Primary Engineering Principles

- Prefer clarity over cleverness.
- Prefer explicit module boundaries over hidden coupling.
- Prefer simple, inspectable data flow over framework-heavy abstraction.
- Prefer correctness, traceability, and reproducibility over premature optimization.

### Code Structure

- Keep modules small and focused around one responsibility.
- Separate ingestion, retrieval, memory, generation, API, and evaluation concerns.
- Use clear function and variable names so the code reads like documentation.
- Avoid large monolithic scripts when reusable modules are more appropriate.
- Introduce shared utilities only after repeated, real duplication appears.

### Comments and Readability

- Use self-documenting code first.
- Be generous with comments where the logic is not obvious.
- Comments are especially encouraged for:
  - retrieval scoring and ranking logic
  - Hopfield-style memory read and write behavior
  - data normalization and schema mapping
  - prompt contracts and output schemas
  - evaluation logic and metrics
  - business rules that affect user-visible behavior
- Avoid trivial comments that only paraphrase code.
- Prefer English comments in source files. If a short bilingual comment helps explain an academic concept, it is acceptable.

### Python Standards

- Use Python for backend services, ingestion scripts, indexing, retrieval, evaluation, and orchestration by default.
- Favor typed function signatures and explicit data models.
- Prefer straightforward packages and modules over magic-heavy meta-programming.
- Keep side effects near the edges of the system.
- Write code that can be followed by a student who knows Python but may not know advanced framework internals.

### JavaScript and TypeScript Standards

- Use JavaScript or TypeScript for frontend work.
- Keep UI components small, readable, and composable.
- Keep client-side data flow explicit.
- Avoid introducing frontend complexity unless it clearly improves the demonstration.
- Add comments where UI state or data transformations are not obvious.

### Documentation Standards

- Durable repository documentation must be bilingual in English and Russian.
- When a change affects architecture, scope, stack, or research framing, update the relevant docs in the same change.
- `docs/DECISIONS.md` is the canonical place for active architectural and scope decisions.
- Plans in `plan/` may guide implementation, but they must not silently override the active decisions file.

### Testing and Verification

- Add tests or smoke checks for core logic whenever practical.
- Prioritize coverage for retrieval, memory selection, normalization, schemas, and evaluation logic.
- Verify behavior close to the changed module, not only through broad end-to-end checks.
- When evaluation fixtures or demo scenarios are user-facing, keep bilingual English and Russian coverage where practical.

### Repository Hygiene

- Keep filenames descriptive and stable.
- Prefer incremental, reviewable changes over large opaque rewrites.
- Do not add dependencies without a clear reason.
- If a dependency is added, document why it is needed.

## Русский

### Основные инженерные принципы

- Предпочитайте ясность излишней изощренности.
- Предпочитайте явные границы модулей скрытой связанности.
- Предпочитайте простой и прозрачный поток данных тяжелой framework-абстракции.
- Предпочитайте корректность, трассируемость и воспроизводимость преждевременной оптимизации.

### Структура кода

- Держите модули небольшими и сфокусированными на одной ответственности.
- Разделяйте ingestion, retrieval, memory, generation, API и evaluation.
- Используйте понятные имена функций и переменных, чтобы код читался как документация.
- Избегайте больших монолитных скриптов, если уместнее переиспользуемые модули.
- Выносите общие утилиты только после появления реального повторения, а не заранее.

### Комментарии и читаемость

- Сначала стремитесь к самодокументируемому коду.
- Щедро добавляйте комментарии там, где логика неочевидна.
- Комментарии особенно рекомендуются для:
  - логики retrieval scoring и ranking
  - поведения Hopfield-style memory при чтении и записи
  - нормализации данных и сопоставления со схемами
  - prompt-контрактов и схем вывода
  - evaluation-логики и метрик
  - бизнес-правил, влияющих на видимое пользователю поведение
- Избегайте тривиальных комментариев, которые лишь пересказывают код.
- В исходном коде предпочтительны комментарии на английском. Если короткий двуязычный комментарий помогает объяснить академическую идею, это допустимо.

### Стандарты Python

- Python используется по умолчанию для backend-сервисов, ingestion-скриптов, indexing, retrieval, evaluation и orchestration.
- Предпочитайте типизированные сигнатуры функций и явные модели данных.
- Отдавайте предпочтение прямолинейным пакетам и модулям вместо избыточной магии и meta-programming.
- Держите side effects ближе к внешним границам системы.
- Пишите код так, чтобы его могла понять студентка, знающая Python, но не обязательно знакомая с внутренностями сложных framework.

### Стандарты JavaScript и TypeScript

- JavaScript или TypeScript используются для frontend-части.
- UI-компоненты должны быть небольшими, читаемыми и композиционными.
- Клиентский поток данных должен быть явным.
- Не добавляйте frontend-сложность без явной пользы для демонстрации проекта.
- Добавляйте комментарии там, где состояние UI или преобразование данных неочевидно.

### Стандарты документации

- Долговечная документация репозитория должна поддерживаться на английском и русском языках.
- Если изменение затрагивает архитектуру, границы продукта, стек или исследовательское позиционирование, соответствующие документы должны обновляться в том же изменении.
- `docs/DECISIONS.md` - каноническое место для активных архитектурных и scope-решений.
- Планы в `plan/` могут направлять реализацию, но не должны молча переопределять активный файл решений.

### Тестирование и проверка

- По возможности добавляйте тесты или smoke-checks для ключевой логики.
- В первую очередь покрывайте retrieval, выбор памяти, нормализацию, схемы и evaluation-логику.
- Проверяйте поведение как можно ближе к измененному модулю, а не только через широкие end-to-end проверки.
- Если evaluation fixtures или demo-сценарии являются user-facing, по возможности поддерживайте двуязычное покрытие на английском и русском языках.

### Гигиена репозитория

- Держите имена файлов описательными и стабильными.
- Предпочитайте небольшие, проверяемые изменения большим непрозрачным переписываниям.
- Не добавляйте зависимости без ясной причины.
- Если зависимость добавлена, задокументируйте, зачем она нужна.
