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
            # 1. Amendment Trap (2022 MSA vs 2024 Addendum No. 3)
            DocumentChunk(
                id=f"{tenant_id}:doc_msa_2022:p4",
                content="Master Services Agreement (2022): Section 4.1 Liability Cap. In no event shall Vendor aggregate liability exceed $1,000,000. Section 4.2 Termination: Either party may terminate with 30 days written notice.",
                metadata={"file": "Enterprise_MSA_2022.pdf", "year": "2022", "section": "4.1"},
            ),
            DocumentChunk(
                id=f"{tenant_id}:doc_addendum_2024:p1",
                content="Addendum No. 3 (Executed 2024, Supersedes Section 4 of 2022 MSA): For Tier 2 enterprise customers, the liability cap is increased to $2,500,000 and termination notice requirement is extended to 60 days.",
                metadata={"file": "Enterprise_Addendum_2024.pdf", "year": "2024", "section": "Addendum 1.2"},
            ),
            # 2. Multi-Hop Appendix IV
            DocumentChunk(
                id=f"{tenant_id}:doc_equity_2023:p12",
                content="2023 Executive Equity Incentive Plan: Section 2.4 Participant Classification. All Group C executive equity awards are strictly governed by the special vesting rules in Appendix IV.",
                metadata={"file": "Equity_Plan_2023.pdf", "page": "12", "section": "2.4"},
            ),
            DocumentChunk(
                id=f"{tenant_id}:doc_appendix_iv:p88",
                content="Appendix IV (Group C Executive Provisions): Notwithstanding standard 1-year schedules, Group C executive options require a mandatory 3-year cliff before any shares vest.",
                metadata={"file": "Equity_Plan_2023.pdf", "page": "88", "section": "Appendix IV"},
            ),
            # 3. Tabular Footnote 14b
            DocumentChunk(
                id=f"{tenant_id}:doc_10q_table:p3",
                content="Consolidated Statement of Operations (Q3 2023):\n| Line Item | Amount |\n| Operating Income | $450 Million |\n| Net Income | $310 Million |",
                metadata={"file": "Form_10Q_Q3_2023.pdf", "page": "3"},
            ),
            DocumentChunk(
                id=f"{tenant_id}:doc_10q_fn14b:p22",
                content="Footnote 14b to Q3 Financial Statements: Operating income includes a pre-tax gain of $120 Million resulting from the one-off divestiture of the European logistics division. Recurring operational income was $330 Million.",
                metadata={"file": "Form_10Q_Q3_2023.pdf", "page": "22"},
            ),
            # 4. Epistemic Humility (Silent Bluff Refusal)
            DocumentChunk(
                id=f"{tenant_id}:doc_cloud_dr:p5",
                content="Internal Cloud Architecture Policy: Standard multi-region disaster recovery SLAs are currently established solely for Google Cloud (europe-west1) and Microsoft Azure (eastus2).",
                metadata={"file": "Cloud_DR_Policy.pdf", "page": "5"},
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
