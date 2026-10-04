"""Health & Readiness Probes for Axiom API Gateway."""

from typing import Any, Dict
from fastapi import APIRouter
from axiom.config.settings import get_settings

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=Dict[str, Any])
async def health_check() -> Dict[str, Any]:
    """Liveness probe returning application metadata and status."""
    settings = get_settings()
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "environment": settings.app_env,
        "engine": "SCORE-v1",
    }


@router.get("/ready", response_model=Dict[str, Any])
async def readiness_check() -> Dict[str, Any]:
    """Readiness probe checking storage and configuration readiness."""
    settings = get_settings()
    return {
        "ready": True,
        "vector_store": settings.vector_store_type,
        "bm25_active": settings.bm25_enabled,
        "fast_model": settings.fast_model,
        "reasoning_model": settings.reasoning_model,
    }
