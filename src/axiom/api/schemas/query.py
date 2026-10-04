"""Query Request & Response Pydantic Schemas for Axiom API."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from axiom.core.state import Citation, StepEvent


class QueryRequest(BaseModel):
    """Payload for submitting a query to Axiom."""
    query: str = Field(..., description="User question or research prompt", min_length=2)
    tenant_id: str = Field(default="default_tenant", description="Enterprise tenant identifier for data isolation")
    user_id: Optional[str] = Field(default="anonymous_user", description="Identifier of the executing user")


class QueryResponse(BaseModel):
    """Full synchronous response payload from Axiom."""
    query: str
    generation: str
    citations: List[Citation] = Field(default_factory=list)
    hallucination_status: str
    fallback_reason: Optional[str] = None
    reasoning_trace: List[StepEvent] = Field(default_factory=list)


class StreamEventData(BaseModel):
    """Payload structure for Server-Sent Events."""
    type: str = Field(description="Event type: 'status' | 'token' | 'citation' | 'done' | 'error'")
    data: Dict[str, Any] = Field(default_factory=dict)
