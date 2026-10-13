"""Unit tests for Knowledge Vault Document Management & Audit Certificate Generation."""

import pytest
from axiom.core.state import DocumentChunk
from axiom.services.audit_exporter import compute_sha256, generate_audit_certificate
from axiom.services.vector_store import HybridVectorStore
from axiom.api.auth import generate_api_key, hash_key, list_api_keys, revoke_api_key


def test_hybrid_vector_store_document_lifecycle():
    """Verify document listing, chunk inspection, and vector purging in HybridVectorStore."""
    store = HybridVectorStore()
    tenant = "test_vault_tenant"

    chunks = [
        DocumentChunk(
            id=f"{tenant}:doc_a.pdf:p1:c1",
            content="Section 1.1: Standard SLA terms for cloud infrastructure.",
            metadata={"file": "doc_a.pdf", "page": 1},
        ),
        DocumentChunk(
            id=f"{tenant}:doc_a.pdf:p2:c2",
            content="Section 2.4: Termination notice is thirty days.",
            metadata={"file": "doc_a.pdf", "page": 2},
        ),
        DocumentChunk(
            id=f"{tenant}:doc_b.md:p1:c1",
            content="System architecture overview and scaling guidelines.",
            metadata={"file": "doc_b.md", "page": 1},
        ),
    ]

    # Ingest chunks
    count = store.ingest_documents(tenant_id=tenant, chunks=chunks)
    assert count == 3

    # 1. Test list_documents
    docs = store.list_documents(tenant_id=tenant)
    assert len(docs) == 2
    doc_map = {d["filename"]: d for d in docs}
    assert "doc_a.pdf" in doc_map
    assert doc_map["doc_a.pdf"]["chunk_count"] == 2
    assert doc_map["doc_a.pdf"]["page_count"] == 2
    assert "doc_b.md" in doc_map
    assert doc_map["doc_b.md"]["chunk_count"] == 1

    # 2. Test get_document_chunks
    chunks_a = store.get_document_chunks(tenant_id=tenant, filename="doc_a.pdf")
    assert len(chunks_a) == 2

    # 3. Test delete_document
    deleted = store.delete_document(tenant_id=tenant, filename="doc_a.pdf")
    assert deleted == 2

    remaining_docs = store.list_documents(tenant_id=tenant)
    assert len(remaining_docs) == 1
    assert remaining_docs[0]["filename"] == "doc_b.md"

    # Search should no longer return purged document
    search_res = store.sparse_search(tenant_id=tenant, query="SLA terms")
    assert not any(c.metadata.get("file") == "doc_a.pdf" for c, _ in search_res)


def test_audit_certificate_generation():
    """Verify SHA-256 cryptographic provenance and certificate formatting."""
    query = "What is the liability cap?"
    generation = "The liability cap is $2,500,000 as defined in Addendum 3. [doc_msa:p1]"
    citations = [
        {
            "source_document": "Addendum_3.pdf",
            "page": 2,
            "relevance_score": 0.98,
            "chunk_id": "c_addendum_3_p2",
            "excerpt": "Under Addendum 3, the total liability cap is revised to $2,500,000.",
        }
    ]

    cert = generate_audit_certificate(
        query=query,
        generation=generation,
        citations=citations,
        tenant_id="tenant_audit_test",
        hallucination_status="grounded",
    )

    assert cert["verdict"] == "grounded"
    assert cert["citation_count"] == 1
    assert "AX-CERT-" in cert["certificate_id"]
    assert len(cert["master_signature"]) == 64  # Valid SHA-256 hex length
    assert "AXIOM ENTERPRISE GROUNDING AUDIT CERTIFICATE" in cert["markdown_content"]
    assert "Addendum_3.pdf" in cert["markdown_content"]


def test_api_key_lifecycle():
    """Verify API key creation, hashing, masking, and revocation."""
    tenant = "tenant_keys_test"
    key_res = generate_api_key(tenant_id=tenant, name="Production Microservice", role="member")

    raw_key = key_res["raw_key"]
    assert raw_key.startswith("ax_live_")
    key_id = key_res["key_id"]

    keys = list_api_keys(tenant_id=tenant)
    assert len(keys) == 1
    assert keys[0]["key_id"] == key_id
    assert "..." in keys[0]["masked_key"]  # Token masked

    # Revoke
    revoked = revoke_api_key(tenant_id=tenant, key_id=key_id)
    assert revoked is True

    keys_after = list_api_keys(tenant_id=tenant)
    assert len(keys_after) == 0
