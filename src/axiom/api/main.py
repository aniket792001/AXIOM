"""Axiom FastAPI Application Entrypoint.

Enterprise API Gateway exposing real-time SSE query streaming,
multi-tenant document ingestion, and health check endpoints.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from axiom.api.routes import chat_router, health_router, ingest_router
from axiom.config.settings import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager for startup and shutdown routines."""
    settings = get_settings()
    print(f"[*] Starting {settings.app_name} on {settings.app_host}:{settings.app_port} [{settings.app_env}]")
    yield
    print(f"[*] Shutting down {settings.app_name}")


def create_app() -> FastAPI:
    """Create and configure the production FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Axiom API",
        description="Production-grade self-correcting RAG platform powered by the SCORE engine.",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Configure CORS for Enterprise Web Clients & Dashboards
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Restrict to trusted domains in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register Routers
    app.include_router(health_router)
    app.include_router(ingest_router)
    app.include_router(chat_router)

    # Static Assets & Verification Dashboard
    ui_dir = Path(__file__).resolve().parent.parent / "ui"
    if ui_dir.exists():
        app.mount("/static", StaticFiles(directory=str(ui_dir)), name="static")

        @app.get("/", include_in_schema=False)
        async def serve_dashboard() -> FileResponse:
            """Serve the Axiom SCORE interactive verification dashboard."""
            return FileResponse(str(ui_dir / "index.html"))

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "axiom.api.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=True if settings.app_env == "development" else False,
    )
