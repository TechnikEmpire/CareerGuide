# Frontend Source Layout

This folder now contains the first implemented UI slice.

Current structure:

- `App.tsx` for the single-page shell and state wiring
- `api/` for backend HTTP bindings
- `components/` for reusable presentation blocks
- `main.tsx` for client bootstrap
- `styles.css` for the current visual system

There is intentionally no router, global store, or frontend-side AI layer yet.
The current UI stays thin and talks directly to the FastAPI backend.

Эта папка теперь уже содержит первый реализованный slice UI.

Текущая структура:

- `App.tsx` для single-page shell и основной wiring логики состояния
- `api/` для HTTP-binding к backend
- `components/` для переиспользуемых UI-блоков
- `main.tsx` для bootstrap клиентского приложения
- `styles.css` для текущей visual-system

Маршрутизатор, global store и frontend-side AI-layer пока намеренно не
добавляются. Текущий UI остается тонким и напрямую работает с FastAPI-backend.
