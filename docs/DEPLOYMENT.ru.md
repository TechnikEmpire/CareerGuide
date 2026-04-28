# Deployment Guide

Последнее обновление: 2026-03-26

## Назначение

Это руководство объясняет самый короткий практический путь деплоя текущего
прототипа CareerGuide.

Активный deployment-baseline теперь такой:

- один Docker-image
- один runtime-container
- один публичный HTTP-port
- собранный frontend раздается FastAPI из того же image
- локальные generator и embedding model artifacts baked into the image
- persistent SQLite-state монтируется отдельно от отслеживаемых retrieval-artifacts

Это намеренно проще, чем multi-container или Kubernetes-setup.

## Что содержит контейнер

Текущий single-image включает:

- FastAPI-backend в [backend/](../backend/)
- собранный React + Vite frontend из [frontend/](../frontend/)
- отслеживаемые retrieval-artifacts в [data/processed/retrieval/](../data/processed/retrieval/)
- отслеживаемый memory-classifier bundle в [tooling/memory_extraction/models/](../tooling/memory_extraction/models/)
- repo-local generator и embedding-модели, которые скачивает [backend/scripts/setup_local_models.py](../backend/scripts/setup_local_models.py)

Во время image-build теперь скачиваются:

- `bartowski/Qwen_Qwen3.5-2B-GGUF` (`Qwen_Qwen3.5-2B-Q4_K_M.gguf`)
- `Qwen/Qwen3-Embedding-0.6B`

Эти модели не отслеживаются в Git. Они подтягиваются во время image-build, чтобы
CI мог собирать deployable artifact из чистого checkout.

## Почему приложение использует один image

Это решение зафиксировано в [docs/DECISIONS.ru.md](DECISIONS.ru.md).

Коротко:

- frontend после `vite build` становится статическим
- backend уже владеет всей логикой retrieval, memory и generation
- прототипу не нужно независимое масштабирование frontend/backend
- single-image — самый быстрый путь к воспроизводимому CPU-deployment

## Файлы, которые определяют deployment-path

- [Dockerfile](../Dockerfile)
- [.dockerignore](../.dockerignore)
- [backend/app/main.py](../backend/app/main.py)
- [backend/app/config.py](../backend/app/config.py)
- [frontend/src/api/client.ts](../frontend/src/api/client.ts)
- [backend/scripts/run_local_app_stack.py](../backend/scripts/run_local_app_stack.py)
- [backend/scripts/setup_local_models.py](../backend/scripts/setup_local_models.py)
- [CI workflow](../.github/workflows/ci.yml)
- [Container image workflow](../.github/workflows/container-image.yml)
- [Deploy workflow](../.github/workflows/deploy.yml)

## Runtime-схема внутри контейнера

Image запускает существующий local app-stack runner:

- [backend/scripts/run_local_app_stack.py](../backend/scripts/run_local_app_stack.py)

Этот скрипт:

1. загружает repo-local runtime-конфигурацию из `.env.local`
2. запускает локальный `llama_cpp.server`
3. ждет, пока generator начнет отвечать на `/v1/models`
4. запускает FastAPI-backend
5. удерживает оба процесса живыми в одном parent-process

Для текущего thesis-prototype это приемлемо, потому что цель здесь —
не production-orchestration platform, а один небольшой inspectable deployment-unit.

## Как раздается frontend

Frontend собирается во время Docker-build и копируется в:

- `/app/frontend/dist`

Backend теперь раздает этот build напрямую из:

- [backend/app/main.py](../backend/app/main.py)

В production:

- browser-запросы к `/` возвращают `frontend/dist/index.html`
- static-asset files из build-dist раздаются напрямую
- API-routes вроде `/chat/answer` и `/career/plan` остаются за backend
- frontend API-calls по умолчанию работают через same-origin, потому что [frontend/src/api/client.ts](../frontend/src/api/client.ts) теперь использует relative base URL вне Vite dev-mode

## Persistent data

Контейнер хранит изменяемое persistent-state по пути:

- `/app/data/runtime/careerguide.db`

Этот путь задается через image-environment в [Dockerfile](../Dockerfile).

Это важно, потому что отслеживаемые retrieval-artifacts остаются по пути:

- `/app/data/processed/retrieval/`

Не монтируйте volume поверх `/app/data/processed`, иначе вы скроете baked-in
FAISS-index и manifest.

Монтировать нужно только runtime-state directory.

## Локальная сборка image

Из корня репозитория:

```bash
docker build -t careerguide:local .
```

Сборка тяжелая. Она скачивает публичные Qwen generator и embedding models и
поэтому создает большой image.

## Локальный запуск image

```bash
docker run --rm \
  -p 8000:8000 \
  -v careerguide-data:/app/data/runtime \
  --name careerguide \
  careerguide:local
```

Затем откройте:

```text
http://127.0.0.1:8000
```

Health-check:

```text
http://127.0.0.1:8000/health
```

## Минимальный путь запуска на Linode

На обычной CPU-VM с установленным Docker самый короткий путь такой:

```bash
docker pull ghcr.io/<OWNER>/careerguide:latest

docker run -d \
  --name careerguide \
  --restart unless-stopped \
  -p 8000:8000 \
  -v /opt/careerguide/data:/app/data/runtime \
  ghcr.io/<OWNER>/careerguide:latest
```

Если нужен TLS и нормальный публичный домен, поставьте на host Caddy или Nginx
перед портом `8000`.

## CI и публикация image

В репозитории теперь есть два GitHub Actions workflow:

- [CI workflow](../.github/workflows/ci.yml)
- [Container image workflow](../.github/workflows/container-image.yml)
- [Deploy workflow](../.github/workflows/deploy.yml)

Поведение такое:

1. `CI` запускает backend-tests и frontend-build на push и pull request.
2. `Container Image` запускается после успешного `CI` на `main` или вручную через
   `workflow_dispatch`.
3. Image публикуется в GHCR как:
   - `ghcr.io/<OWNER>/careerguide:latest`
   - `ghcr.io/<OWNER>/careerguide:sha-<commit>`
4. `Deploy` запускается после успешного `Container Image` на `main`, подключается
   по SSH к Linode-хосту, тянет новый `:latest` image и пересоздает app-service.

## Secrets репозитория для автоматического деплоя

Для нового deploy-workflow задайте такие repository secrets:

- `DEPLOY_HOST`
- `DEPLOY_PORT`
- `DEPLOY_USER`
- `DEPLOY_SSH_KEY`

Рекомендуемые значения для этого проекта:

- `DEPLOY_HOST` = `careerplan.builders`
- `DEPLOY_PORT` = ваш hardened SSH-port, например `2222`
- `DEPLOY_USER` = `deploy`
- `DEPLOY_SSH_KEY` = полное содержимое private-key для SSH-ключа пользователя `deploy`

Если GHCR-package приватный, добавьте также:

- `GHCR_USERNAME`
- `GHCR_TOKEN`

Если GHCR-package публичный, эти два registry-secret не нужны.

## Что делает deploy-workflow

Deploy-workflow:

1. подключается к Linode-хосту по SSH как пользователь deploy
2. при наличии registry-secret при необходимости логинится в GHCR
3. выполняет `docker compose pull app`
4. выполняет `docker compose up -d app`
5. очищает старые dangling images

Это намеренно простой механизм. Сервер уже хранит `compose.yaml`,
`Caddyfile` и локальные runtime-override файлы, поэтому workflow лишь
обновляет app-image и оставляет reverse-proxy нетронутым.

## Операционные оговорки

- Image намеренно большой, потому что он включает локальный Qwen GGUF
  generator и Qwen embedding-model.
- Startup медленнее, чем у маленького stateless web-container, потому что
  сначала должен подняться локальный generator-process.
- Это baseline CPU-only deployment, поэтому модель будет функциональной, но не быстрой.
- Retrieval-index уже baked into the image, но runtime SQLite database по умолчанию
  начинается пустой, если вы не смонтируете существующее состояние.
- Deploy-workflow обновляет только `app` service. Это сделано специально,
  потому что Caddy-конфигурация хранится локально на сервере, а не в репозитории.

## Рекомендуемые минимальные operator-checks

После свежего deployment проверьте:

1. `GET /health` возвращает `200`
2. web UI загружается с `/`
3. `POST /chat/answer` возвращает grounded answer
4. `POST /career/plan` возвращает structured plan
5. memory переживает перезапуск контейнера, если смонтирован `/app/data/runtime`
