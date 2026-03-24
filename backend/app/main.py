"""FastAPI application entry point."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api import assistant, eval as eval_api, memory, retrieval
from backend.app.config import settings
from backend.db.session import init_db


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
    return app


app = create_app()
