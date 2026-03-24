# Frontend Source Layout

This folder contains the implemented frontend application.

Current structure:

- `App.tsx` for the single-page shell, local state, and page-level orchestration
- `api/` for backend HTTP bindings and shared frontend response types
- `components/` for reusable presentation blocks such as messages, citations, and memory panels
- `main.tsx` for client bootstrap
- `styles.css` for the current visual system and shell layout

There is intentionally no router, global store, or frontend-side AI layer yet.
The UI remains thin and talks directly to the FastAPI backend.
