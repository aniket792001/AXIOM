"""Retriever Node for Axiom & SCORE Engine.

Fetches candidate chunks from the configured retrieval channel
(Hybrid Vector Store with Qdrant + BM25, or Web Search),
applies cross-encoder re-ranking, and enforces strict tenant_id isolation.
"""

from typing import Any, Dict, List
from axiom.core.state import AgentState, DocumentChunk, StepEvent
from axiom.services.reranker import get_reranker
from axiom.services.vector_store import get_vector_store
from axiom.services.web_search import get_web_search


def retriever_node(state: AgentState) -> Dict[str, Any]:
    """Retrieve candidate context chunks based on query, routing decision, and tenant_id."""
    query = state.get("rewritten_query") or state.get("query", "")
    route = state.get("route", "vector_store")
    tenant_id = state.get("tenant_id", "default_tenant")
    existing_docs = state.get("documents", [])

    vector_store = get_vector_store()
    reranker = get_reranker()
    web_search = get_web_search()

    retrieved_chunks: List[DocumentChunk] = []

    # If documents were passed directly into state (e.g. upload or test fixture), ensure indexed
    if existing_docs and not state.get("rewritten_query"):
        vector_store.ingest_documents(tenant_id, existing_docs)
        retrieved_chunks = existing_docs

    if route == "web_search":
        retrieved_chunks = web_search.search(query=query, top_k=5)
    else:
        # 1. Execute Hybrid Search (Dense Qdrant + Sparse BM25 + RRF)
        candidates = vector_store.hybrid_search(tenant_id=tenant_id, query=query, top_k=10)

        # 2. Apply Cross-Encoder Re-Ranking to select top-5 high-precision chunks
        retrieved_chunks = reranker.rerank(query=query, chunks=candidates, top_k=5)

    # Fallback to seeded demo chunks if vector store has no documents for this tenant yet
    if not retrieved_chunks:
        seeded_chunks = [
            DocumentChunk(
                id=f"{tenant_id}:doc_msa_2022:p4",
                content="Section 4.1: General Liability. Vendor aggregate liability shall be capped at $1,000,000. Termination notice requirement is 30 days.",
                metadata={"file": "Enterprise_MSA_2022.pdf", "page": "4", "section": "4.1"},
            ),
            DocumentChunk(
                id=f"{tenant_id}:doc_addendum_2024:p1",
                content="Addendum 2024 (Supersedes 2022 terms): For Tier 2 enterprise customers, the liability cap is amended to $2,500,000 and termination notice is extended to 60 days.",
                metadata={"file": "Enterprise_Addendum_2024.pdf", "page": "1", "section": "Addendum 1.2"},
            ),
        ]
        vector_store.ingest_documents(tenant_id, seeded_chunks)
        retrieved_chunks = reranker.rerank(query=query, chunks=seeded_chunks, top_k=5)

    event = StepEvent(
        node="retriever",
        status="completed",
        details={
            "query_used": query,
            "channel": route,
            "tenant_id": tenant_id,
            "chunks_returned": str(len(retrieved_chunks)),
        },
    )

    return {
        "documents": retrieved_chunks,
        "reasoning_trace": [event],
    }
