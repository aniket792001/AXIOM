"""Document Ingestion Routes for Axiom API Gateway."""

from fastapi import APIRouter, HTTPException, status
from axiom.api.schemas.ingest import IngestRequest, IngestResponse
from axiom.services.vector_store import get_vector_store

router = APIRouter(prefix="/api/v1", tags=["Ingestion"])


@router.post("/ingest", response_model=IngestResponse, status_code=status.HTTP_201_CREATED)
async def ingest_documents(payload: IngestRequest) -> IngestResponse:
    """Ingest document chunks into both dense vector store and sparse BM25 index with tenant isolation."""
    if not payload.documents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one DocumentChunk must be provided for ingestion.",
        )

    store = get_vector_store()
    count = store.ingest_documents(tenant_id=payload.tenant_id, chunks=payload.documents)

    return IngestResponse(
        tenant_id=payload.tenant_id,
        ingested_count=count,
        status="success",
    )
