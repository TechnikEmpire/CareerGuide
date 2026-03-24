# CareerGuide Frontend

Этот каталог содержит первый реальный baseline web UI для CareerGuide.

Текущий stack:

- React
- TypeScript
- Vite

Текущий scope:

- выбор профиля через поле user-id
- grounded-chat через `POST /chat/answer`
- отображение citations
- отображение “memory used” из answer-response
- structured plan generation через `POST /career/plan`
- memory inspection через `GET /memory/list`

Локальные команды:

```bash
cd frontend
npm install
npm run dev
```

Проверка production-сборки:

```bash
cd frontend
npm run build
```

URL frontend по умолчанию:

```text
http://127.0.0.1:5173
```

Backend URL по умолчанию, который ожидает frontend:

```text
http://127.0.0.1:8000
```

Если backend работает в другом месте, задайте `VITE_API_BASE_URL` перед
запуском dev-server.
