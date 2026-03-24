# CareerGuide Frontend

This directory contains the first real web UI baseline for CareerGuide.

Current stack:

- React
- TypeScript
- Vite

Current scope:

- profile selection through a user-id field
- grounded chat via `POST /chat/answer`
- citation display
- “memory used” display from the answer response
- structured plan generation via `POST /career/plan`
- memory inspection via `GET /memory/list`

Local commands:

```bash
cd frontend
npm install
npm run dev
```

Production build check:

```bash
cd frontend
npm run build
```

Default frontend URL:

```text
http://127.0.0.1:5173
```

Default backend URL expected by the frontend:

```text
http://127.0.0.1:8000
```

If the backend runs elsewhere, set `VITE_API_BASE_URL` before starting the dev
server.
