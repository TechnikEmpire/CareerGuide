# Deployment Guide

Last updated: 2026-03-24

## Purpose

This guide explains the shortest practical deployment path for the current
CareerGuide prototype.

The active deployment baseline is now:

- one Docker image
- one runtime container
- one public HTTP port
- built frontend served by FastAPI from the same image
- local generator and embedding model artifacts baked into the image
- persistent SQLite state mounted separately from the tracked retrieval assets

This is intentionally simpler than a multi-container or Kubernetes setup.

## What The Container Contains

The current single image includes:

- the FastAPI backend under [backend/](../backend/)
- the built React + Vite frontend from [frontend/](../frontend/)
- the tracked retrieval artifacts in [data/processed/retrieval/](../data/processed/retrieval/)
- the tracked memory classifier bundle in [tooling/memory_extraction/models/](../tooling/memory_extraction/models/)
- the repo-local generator and embedding models downloaded by [backend/scripts/setup_local_models.py](../backend/scripts/setup_local_models.py)

The image build now downloads:

- `ggml-org/Qwen3-0.6B-GGUF`
- `Qwen/Qwen3-Embedding-0.6B`

Those models are not tracked in Git. They are pulled during the image build so
CI can produce a deployable artifact from a clean checkout.

## Why The App Uses One Image

This decision is recorded in [docs/DECISIONS.en.md](DECISIONS.en.md).

The short version is:

- the frontend is static after `vite build`
- the backend already owns all retrieval, memory, and generation logic
- the prototype does not need independent frontend/backend scaling
- a single image is the fastest path to a reproducible CPU deployment

## Files That Define The Deployment Path

- [Dockerfile](../Dockerfile)
- [.dockerignore](../.dockerignore)
- [backend/app/main.py](../backend/app/main.py)
- [backend/app/config.py](../backend/app/config.py)
- [frontend/src/api/client.ts](../frontend/src/api/client.ts)
- [backend/scripts/run_local_app_stack.py](../backend/scripts/run_local_app_stack.py)
- [backend/scripts/setup_local_models.py](../backend/scripts/setup_local_models.py)
- [CI workflow](../.github/workflows/ci.yml)
- [Container image workflow](../.github/workflows/container-image.yml)

## Runtime Shape Inside The Container

The image starts the existing local app-stack runner:

- [backend/scripts/run_local_app_stack.py](../backend/scripts/run_local_app_stack.py)

That script:

1. loads the repo-local runtime configuration from `.env.local`
2. starts the local `llama_cpp.server`
3. waits for the generator to answer on `/v1/models`
4. starts the FastAPI backend
5. keeps both processes alive in one parent process

This is acceptable for the current thesis prototype because the goal is one
small inspectable deployment unit, not a production orchestration platform.

## Frontend Serving Model

The frontend is built during the Docker build and copied into
`/app/frontend/dist`.

The backend now serves that build directly from:

- [backend/app/main.py](../backend/app/main.py)

In production:

- browser requests for `/` return `frontend/dist/index.html`
- static asset files under the built dist are served directly
- API routes such as `/chat/answer` and `/career/plan` stay backend-owned
- frontend API calls default to same-origin because [frontend/src/api/client.ts](../frontend/src/api/client.ts) now uses a relative base URL outside Vite dev mode

## Persistent Data

The container keeps persistent mutable state under:

- `/app/data/runtime/careerguide.db`

That path is set through the image environment in [Dockerfile](../Dockerfile).

This separation matters because the tracked retrieval artifacts remain under:

- `/app/data/processed/retrieval/`

Do not mount a volume over `/app/data/processed`, or you will hide the baked-in
FAISS index and manifest.

Mount only the runtime state directory.

## Build The Image Locally

From the repository root:

```bash
docker build -t careerguide:local .
```

This build is heavy. It downloads the public Qwen generator and embedding
models and therefore produces a large image.

## Run The Image Locally

```bash
docker run --rm \
  -p 8000:8000 \
  -v careerguide-data:/app/data/runtime \
  --name careerguide \
  careerguide:local
```

Then open:

```text
http://127.0.0.1:8000
```

Health check:

```text
http://127.0.0.1:8000/health
```

## Minimal Linode Run Path

On a plain CPU VM with Docker installed, the shortest path is:

```bash
docker pull ghcr.io/<OWNER>/careerguide:latest

docker run -d \
  --name careerguide \
  --restart unless-stopped \
  -p 8000:8000 \
  -v /opt/careerguide/data:/app/data/runtime \
  ghcr.io/<OWNER>/careerguide:latest
```

If you want TLS and a normal public domain, put Caddy or Nginx on the host in
front of port `8000`.

## CI And Image Publishing

The repository now has two GitHub Actions workflows:

- [CI workflow](../.github/workflows/ci.yml)
- [Container image workflow](../.github/workflows/container-image.yml)

The behavior is:

1. `CI` runs backend tests and the frontend build on pushes and pull requests.
2. `Container Image` runs after `CI` succeeds on `main`, or manually through
   `workflow_dispatch`.
3. The image is published to GHCR as:
   - `ghcr.io/<OWNER>/careerguide:latest`
   - `ghcr.io/<OWNER>/careerguide:sha-<commit>`

## What CI Does Not Yet Automate

The current baseline stops at a published image.

It does **not** yet automatically:

- SSH into the Linode server
- pull the new image on the host
- restart the running container

That last step is now optional deployment polish, not a blocker for having a
real deployable container pipeline.

## Operational Caveats

- The image is intentionally large because it bakes in the local Qwen GGUF
  generator and the Qwen embedding model.
- Startup is slower than a small stateless web container because the local
  generator process must come online first.
- This is a CPU-only deployment baseline, so the model will be functional but
  not fast.
- The retrieval index is already baked into the image, but the runtime SQLite
  database starts empty unless you mount existing state.

## Recommended Minimum Operator Checks

After a fresh deployment, verify:

1. `GET /health` returns `200`
2. the web UI loads from `/`
3. `POST /chat/answer` returns a grounded answer
4. `POST /career/plan` returns a structured plan
5. memory survives a container restart when `/app/data/runtime` is mounted
