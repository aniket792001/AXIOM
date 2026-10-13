"""Axiom API Route Handlers."""

from axiom.api.routes.auth import router as auth_router
from axiom.api.routes.health import router as health_router
from axiom.api.routes.ingest import router as ingest_router
from axiom.api.routes.chat import router as chat_router
from axiom.api.routes.documents import router as documents_router
from axiom.api.routes.contradiction import router as contradiction_router
from axiom.api.routes.export import router as export_router
from axiom.api.routes.keys import router as keys_router
from axiom.api.routes.benchmark import router as benchmark_router

__all__ = [
    "auth_router",
    "health_router",
    "ingest_router",
    "chat_router",
    "documents_router",
    "contradiction_router",
    "export_router",
    "keys_router",
    "benchmark_router",
]
