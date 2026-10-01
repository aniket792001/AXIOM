"""Axiom & SCORE AgentState Definition.

Typed schema for the LangGraph state machine.
Supports multi-tenancy, deterministic citations, and reasoning event traces.
"""

from operator import add
from typing import Annotated, Dict, List, Optional
from pydantic import BaseModel, Field
from typing_extensions import TypedDict


class DocumentChunk(BaseModel):
    """Represents an ingested or retrieved document snippet."""
    id: str = Field(description="Unique chunk identifier, e.g. doc123:chunk4")
    content: str = Field(description="Extracted text or markdown content")
    metadata: Dict[str, str] = Field(default_factory=dict, description="Metadata: file, page, section")
    relevance_score: Optional[float] = Field(default=None, description="Calculated relevance or rerank score")


class Citation(BaseModel):
    """Verifiable citation linking a generated statement to source context."""
    doc_id: str = Field(description="Source document name or ID")
    chunk_id: str = Field(description="Specific chunk ID cited")
    quote: str = Field(description="Exact quote or snippet verifying the claim")


class StepEvent(BaseModel):
    """Real-time event emitted during node execution for SSE streaming."""
    node: str = Field(description="Name of the executing node")
    status: str = Field(description="Event status: started, completed, retry, filtered")
    details: Dict[str, str] = Field(default_factory=dict, description="Structured diagnostics")


class AgentState(TypedDict):
    """The central state schema for Axiom's SCORE LangGraph engine.

    Passed across all nodes and serializable to Redis/Postgres checkpointers.
    """
    # Multi-Tenant & Identity Isolation (Essential for 1M Customers)
    tenant_id: str
    user_id: str

    # User Input & Query Evolution
    query: str
    rewritten_query: Optional[str]

    # Routing Decision
    route: str  # "vector_store" | "web_search" | "direct"

    # Context & Retrieval Pools
    documents: List[DocumentChunk]
    graded_documents: List[DocumentChunk]

    # Generation & Grounding
    generation: str
    citations: List[Citation]

    # Evaluation States
    hallucination_status: str  # "grounded" | "hallucinated" | "pending"
    relevance_status: str      # "relevant" | "irrelevant" | "pending"

    # Self-Correction Guardrails
    loop_count: int
    fallback_reason: Optional[str]

    # Cumulative Diagnostics (appended using operator.add)
    reasoning_trace: Annotated[List[StepEvent], add]
