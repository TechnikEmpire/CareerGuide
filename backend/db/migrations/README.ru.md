# Database Migrations

Сейчас backend сохраняет persistence максимально простым.

Инициализация схемы SQLite происходит автоматически при startup, и активного
Alembic-workflow пока нет.

Вводите Alembic или другую migration-system только тогда, когда схема начнет
меняться настолько часто, что handwritten startup-initialization перестанет
быть читаемой или безопасной.
