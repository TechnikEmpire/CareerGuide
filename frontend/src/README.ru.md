# Frontend Source Layout

Эта папка содержит реализованное frontend-приложение.

Текущая структура:

- `App.tsx` для single-page shell, local state и page-level orchestration
- `api/` для backend HTTP-bindings и общих frontend-типов response
- `config/` для language-specific UI-copy и frontend-side language helpers
- `components/` для переиспользуемых UI-блоков, таких как messages, citations и memory-panels
- `main.tsx` для bootstrap клиентского приложения
- `test/` для frontend test-setup helpers
- `styles.css` для текущей visual-system и shell-layout

Маршрутизатор, global store и frontend-side AI-layer пока намеренно не
добавляются. UI остается тонким и напрямую работает с FastAPI-backend.
