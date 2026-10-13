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
        assert 'id="root"' in content
        assert "app.jsx" in content


@pytest.mark.asyncio
async def test_dashboard_static_assets():
    """Verify that styles.css and app.jsx are correctly served over /static/."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Check CSS
        css_resp = await client.get("/static/styles.css")
        assert css_resp.status_code == 200
        assert "text/css" in css_resp.headers.get("content-type", "")
        assert "--bg-canvas" in css_resp.text
        assert '[data-theme="light"]' in css_resp.text

        # Check React JSX
        jsx_resp = await client.get("/static/app.jsx")
        assert jsx_resp.status_code == 200
        assert "AxiomApp" in jsx_resp.text
        assert "query/stream" in jsx_resp.text
