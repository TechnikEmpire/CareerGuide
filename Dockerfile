# syntax=docker/dockerfile:1.7

FROM node:20-bookworm-slim AS frontend-build

WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci

COPY frontend/ ./
RUN npm run build


FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/root/.cache/huggingface \
    CAREERGUIDE_APP_ENV=production \
    CAREERGUIDE_DEBUG=false \
    CAREERGUIDE_DATABASE_URL=sqlite:////app/data/runtime/careerguide.db

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        cmake \
        curl \
        git \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements-runtime.txt ./
RUN --mount=type=cache,target=/root/.cache/pip \
    python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt -r requirements-runtime.txt

COPY . .
COPY --from=frontend-build /app/frontend/dist /app/frontend/dist

RUN mkdir -p /app/data/runtime

RUN --mount=type=cache,target=/root/.cache/huggingface \
    python -m backend.scripts.setup_local_models

EXPOSE 8000
VOLUME ["/app/data/runtime"]

HEALTHCHECK --interval=30s --timeout=10s --start-period=180s --retries=5 \
  CMD curl --fail --silent http://127.0.0.1:8000/health || exit 1

CMD ["python", "-m", "backend.scripts.run_local_app_stack", "--host", "0.0.0.0", "--port", "8000"]
