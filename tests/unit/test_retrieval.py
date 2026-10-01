"""Unit tests for Axiom Multi-Tenant Hybrid Retrieval & Re-ranking."""

import pytest
from axiom.core.state import DocumentChunk
from axiom.services.vector_store import get_vector_store
from axiom.services.reranker import get_reranker
from axiom.services.web_search import get_web_search


def test_multi_tenant_isolation():
    """Verify that Tenant A cannot retrieve Tenant B's confidential documents."""
    store = get_vector_store()

    tenant_a_chunks = [
        DocumentChunk(
            id="tenant_a_doc1",
            content="Confidential payroll data for Tenant A: CEO compensation is $500k.",
            metadata={"confidential": "true"},
        )
    ]
    tenant_b_chunks = [
        DocumentChunk(
            id="tenant_b_doc1",
            content="Confidential patent formula for Tenant B: Superconductor alloy recipe.",
            metadata={"confidential": "true"},
        )
    ]

    store.ingest_documents("tenant_a", tenant_a_chunks)
    store.ingest_documents("tenant_b", tenant_b_chunks)

    # Search as Tenant A
    results_a = store.hybrid_search(tenant_id="tenant_a", query="compensation payroll", top_k=5)
    chunk_ids_a = [c.id for c in results_a]

    assert "tenant_a_doc1" in chunk_ids_a
    assert "tenant_b_doc1" not in chunk_ids_a

    # Search as Tenant B
    results_b = store.hybrid_search(tenant_id="tenant_b", query="superconductor formula", top_k=5)
    chunk_ids_b = [c.id for c in results_b]

    assert "tenant_b_doc1" in chunk_ids_b
    assert "tenant_a_doc1" not in chunk_ids_b


def test_bm25_exact_keyword_matching():
    """Verify that BM25 catches exact alphanumeric clause numbers that vector search misses."""
    store = get_vector_store()

    contract_chunks = [
        DocumentChunk(
            id="clause_4_1_b",
            content="Section 4.1(b): Force Majeure events include earthquakes and floods.",
            metadata={"section": "4.1(b)"},
        ),
        DocumentChunk(
            id="clause_9_2",
            content="Section 9.2: Arbitration shall take place in Delaware.",
            metadata={"section": "9.2"},
        ),
    ]

    store.ingest_documents("tenant_legal", contract_chunks)

    # Exact clause query
    sparse_matches = store.sparse_search(tenant_id="tenant_legal", query="4.1(b)", top_k=2)
    assert len(sparse_matches) > 0
    assert sparse_matches[0][0].id == "clause_4_1_b"


def test_reranker_amendment_prioritization():
    """Verify that re-ranker boosts superseding addendums over initial agreements."""
    reranker = get_reranker()

    chunks = [
        DocumentChunk(
            id="old_contract",
            content="2022 Master Agreement: Liability is $1,000,000.",
        ),
        DocumentChunk(
            id="new_addendum",
            content="2024 Addendum (Supersedes 2022): Tier 2 liability is $2,500,000.",
        ),
    ]

    reranked = reranker.rerank(query="liability amendment Tier 2", chunks=chunks, top_k=2)

    assert len(reranked) == 2
    # The new addendum should be prioritized first
    assert reranked[0].id == "new_addendum"


def test_web_search_fallback():
    """Verify that web search returns valid structured DocumentChunks."""
    web_service = get_web_search()
    results = web_service.search(query="current stock market inflation", top_k=3)

    assert len(results) > 0
    assert isinstance(results[0], DocumentChunk)
    assert "web:" in results[0].id
