"""Integration tests for Axiom FastAPI Gateway & Real-Time SSE Streaming."""

import json
import pytest
from httpx import ASGITransport, AsyncClient
from axiom.api.main import app
from axiom.core.state import DocumentChunk


@pytest.mark.anyio
async def test_health_endpoints():
    """Verify health and readiness probes."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        health_resp = await client.get("/health")
        assert health_resp.status_code == 200
        assert health_resp.json()["status"] == "healthy"

        ready_resp = await client.get("/ready")
        assert ready_resp.status_code == 200
        assert ready_resp.json()["ready"] is True


@pytest.mark.anyio
async def test_ingest_and_query_flow():
    """Verify end-to-end document ingestion followed by synchronous query."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Ingest document
        ingest_payload = {
            "tenant_id": "tenant_api_test",
            "documents": [
                {
                    "id": "tenant_api_test:clause_5",
                    "content": "Section 5: Customer shall receive 24/7 dedicated support under enterprise SLA.",
                    "metadata": {"section": "5"},
                }
            ],
        }
        ingest_resp = await client.post("/api/v1/ingest", json=ingest_payload)
        assert ingest_resp.status_code == 201
        assert ingest_resp.json()["ingested_count"] == 1

        # 2. Query document
        query_payload = {
            "query": "What support is provided under enterprise SLA?",
            "tenant_id": "tenant_api_test",
        }
        query_resp = await client.post("/api/v1/query", json=query_payload)
        assert query_resp.status_code == 200
        data = query_resp.json()
        assert data["generation"] != ""
        assert data["hallucination_status"] == "grounded"


@pytest.mark.anyio
async def test_sse_query_streaming():
    """Verify real-time Server-Sent Events (SSE) stream emits status, answer, and done events."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        stream_payload = {
            "query": "What is the liability cap under the addendum?",
            "tenant_id": "tenant_stream_test",
        }
        response = await client.post("/api/v1/query/stream", json=stream_payload)
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")

        raw_events = response.text
        # Verify event types were emitted
        assert "event: status" in raw_events
        assert "event: done" in raw_events
