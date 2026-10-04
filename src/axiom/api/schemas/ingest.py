"""Ingestion Request & Response Pydantic Schemas for Axiom API."""

from typing import List
from pydantic import BaseModel, Field
from axiom.core.state import DocumentChunk


class IngestRequest(BaseModel):
    """Payload for indexing document chunks into Axiom's hybrid vector store."""
    tenant_id: str = Field(..., description="Target tenant ID for partition isolation")
    documents: List[DocumentChunk] = Field(..., description="List of DocumentChunks to index", min_length=1)


class IngestResponse(BaseModel):
    """Response returned upon successful document chunk indexing."""
    tenant_id: str
    ingested_count: int
    status: str = Field(default="success")
