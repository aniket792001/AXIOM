"""Integration tests for Axiom Interactive Verification Dashboard static file serving."""

import pytest
from httpx import ASGITransport, AsyncClient
from axiom.api.main import app


@pytest.mark.asyncio
async def test_dashboard_index_serving():
    """Verify that root GET / serves the interactive verification dashboard HTML."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
        content = response.text
        assert "AXIOM" in content
        assert "SCORE ENGINE" in content
        assert "pipeline-steps" in content
        assert "verdict-tag" in content


@pytest.mark.asyncio
async def test_dashboard_static_assets():
    """Verify that styles.css and app.js are correctly served over /static/."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Check CSS
        css_resp = await client.get("/static/styles.css")
        assert css_resp.status_code == 200
        assert "text/css" in css_resp.headers.get("content-type", "")
        assert "--bg-canvas: #0A192F" in css_resp.text

        # Check JS
        js_resp = await client.get("/static/app.js")
        assert js_resp.status_code == 200
        assert "Axiom SCORE Engine" in js_resp.text
        assert "query/stream" in js_resp.text
