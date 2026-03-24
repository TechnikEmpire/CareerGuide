"""FastAPI application entry point."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from backend.app.api import assistant, eval as eval_api, memory, retrieval
from backend.app.config import settings
from backend.db.session import init_db

RESERVED_FRONTEND_PATHS = {
    "chat",
    "career",
    "memory",
    "retrieval",
    "eval",
    "health",
    "docs",
    "redoc",
    "openapi.json",
}


def _configure_frontend_routes(app: FastAPI) -> None:
    """Serve the built frontend SPA from the backend when a dist folder exists.

    The production deployment path keeps the frontend and backend in one image.
    Exact API routes stay registered first; this fallback only handles browser
    requests for the built React assets and the SPA shell.
    """

    if not settings.serve_frontend:
        return

    dist_path = settings.frontend_dist_path
    index_path = dist_path / "index.html"
    if not index_path.exists():
        return

    def _resolve_static_file(relative_path: str) -> Path | None:
        candidate = (dist_path / relative_path).resolve()
        try:
            candidate.relative_to(dist_path.resolve())
        except ValueError:
            return None
        if candidate.is_file():
            return candidate
        return None

    @app.get("/", include_in_schema=False)
    def frontend_index() -> FileResponse:
        return FileResponse(index_path)

    @app.get("/{full_path:path}", include_in_schema=False)
    def frontend_entrypoint(full_path: str) -> FileResponse:
        static_file = _resolve_static_file(full_path)
        if static_file is not None:
            return FileResponse(static_file)

        first_segment = full_path.split("/", 1)[0]
        if first_segment in RESERVED_FRONTEND_PATHS:
            raise HTTPException(status_code=404, detail="Not found.")
        return FileResponse(index_path)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        debug=settings.debug,
        summary="Academic proof-of-concept backend for grounded career guidance.",
    )

    if settings.frontend_dev_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.frontend_dev_origins,
            allow_credentials=False,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    @app.on_event("startup")
    def on_startup() -> None:
        # The MVP keeps persistence simple and local. Initializing the SQLite
        # schema on startup keeps the first developer experience friction-free.
        init_db()

    @app.get("/health", tags=["system"])
    def healthcheck() -> dict[str, str]:
        """Return a minimal service health signal."""

        return {
            "status": "ok",
            "app": settings.app_name,
            "environment": settings.app_env,
        }

    app.include_router(assistant.router)
    app.include_router(retrieval.router)
    app.include_router(memory.router)
    app.include_router(eval_api.router)
    _configure_frontend_routes(app)
    return app


app = create_app()
