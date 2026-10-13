"""Integration tests for Knowledge Vault, Export, and API Key REST endpoints."""

import pytest
from fastapi.testclient import TestClient
from axiom.api.main import app

client = TestClient(app)


def test_vault_documents_endpoints():
    """Verify document upload, listing, chunk inspection, and deletion."""
    tenant = "api_vault_test"

    # 1. Ingest a document file
    file_content = b"# Master Services Agreement\n\nSection 14.2: Governing law is Delaware State Law.\n\nSection 14.3: Notices require written confirmation."
    upload_res = client.post(
        "/api/v1/ingest/file",
        data={"tenant_id": tenant},
        files={"file": ("msa_contract.md", file_content, "text/markdown")},
    )
    assert upload_res.status_code == 201
    assert upload_res.json()["status"] == "success"

    # 2. List documents
    list_res = client.get(f"/api/v1/documents?tenant_id={tenant}")
    assert list_res.status_code == 200
    docs = list_res.json()
    assert len(docs) >= 1
    assert any(d["filename"] == "msa_contract.md" for d in docs)

    # 3. Inspect chunks
    chunks_res = client.get(f"/api/v1/documents/msa_contract.md/chunks?tenant_id={tenant}")
    assert chunks_res.status_code == 200
    chunks = chunks_res.json()
    assert len(chunks) >= 1

    # 3.1 Verify document structured view for visualizer
    view_res = client.get(f"/api/v1/documents/msa_contract.md/view?tenant_id={tenant}")
    assert view_res.status_code == 200
    view_data = view_res.json()
    assert view_data["filename"] == "msa_contract.md"
    assert view_data["total_pages"] >= 1
    assert view_data["total_chunks"] >= 1
    assert len(view_data["sha256"]) == 64
    assert len(view_data["pages"]) >= 1

    # 3.2 Verify document raw text
    raw_res = client.get(f"/api/v1/documents/msa_contract.md/raw?tenant_id={tenant}")
    assert raw_res.status_code == 200
    assert "Delaware State Law" in raw_res.json()["content"]

    # 4. Delete document
    del_res = client.delete(f"/api/v1/documents/msa_contract.md?tenant_id={tenant}")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "success"

    # 5. Verify deletion
    list_after = client.get(f"/api/v1/documents?tenant_id={tenant}")
    assert not any(d["filename"] == "msa_contract.md" for d in list_after.json())


def test_export_audit_certificate_endpoint():
    """Verify export certificate endpoint returns valid Markdown attachment."""
    payload = {
        "query": "What is the notice period?",
        "generation": "Notice period is 30 days. [c1]",
        "citations": [{"source_document": "contract.pdf", "page": 1, "excerpt": "Notice is 30 days."}],
        "tenant_id": "test_export_tenant",
        "format": "markdown",
    }
    res = client.post("/api/v1/export/certificate", json=payload)
    assert res.status_code == 200
    assert "text/markdown" in res.headers["content-type"]
    assert "AXIOM ENTERPRISE GROUNDING AUDIT CERTIFICATE" in res.text


def test_keys_endpoints_lifecycle():
    """Verify key generation, listing, and revocation via REST API."""
    tenant = "api_key_test_tenant"

    # 1. Create Key
    create_res = client.post(
        "/api/v1/keys",
        json={"name": "Integration Key", "tenant_id": tenant, "role": "admin"},
    )
    assert create_res.status_code == 201
    key_data = create_res.json()
    assert "raw_key" in key_data
    assert key_data["raw_key"].startswith("ax_live_")
    key_id = key_data["key_id"]

    # 2. List Keys
    list_res = client.get(f"/api/v1/keys?tenant_id={tenant}")
    assert list_res.status_code == 200
    keys = list_res.json()
    assert len(keys) == 1
    assert keys[0]["key_id"] == key_id

    # 3. Revoke Key
    del_res = client.delete(f"/api/v1/keys/{key_id}?tenant_id={tenant}")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "success"
