# Database Migrations

The backend currently keeps persistence simple.

SQLite schema initialization happens automatically on startup, and there is no
active Alembic workflow yet.

Introduce Alembic or another migration system only if the schema begins to
change often enough that handwritten startup initialization is no longer
readable or safe.
