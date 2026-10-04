"""Axiom API Route Handlers."""

from axiom.api.routes.health import router as health_router
from axiom.api.routes.ingest import router as ingest_router
from axiom.api.routes.chat import router as chat_router

__all__ = [
    "health_router",
    "ingest_router",
    "chat_router",
]
