"""Contract Contradiction & Amendment Diff API Routes for Axiom Platform."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Header, Query
from pydantic import BaseModel, Field

from axiom.services.contradiction_service import (
    DEMO_CONTRACT_A,
    DEMO_CONTRACT_B,
    analyze_contract_contradiction,
)

router = APIRouter(prefix="/api/v1/contradiction", tags=["Contract Contradiction & Diff"])


class ClauseDetail(BaseModel):
    """Detailed clause excerpt and section citation."""
    text: str
    section: str
    page: Optional[int] = 1


class ContradictionItem(BaseModel):
    """Single category comparison item in the contradiction matrix."""
    category: str
    status: str = Field(..., description="CONTRADICTION | MODIFICATION | CONSISTENT")
    risk_level: str = Field(..., description="HIGH | MEDIUM | LOW")
    doc_a_clause: Dict[str, Any]
    doc_b_clause: Dict[str, Any]
    analysis: str
    precedence_ruling: str


class ContradictionRequest(BaseModel):
    """Payload for comparing two contracts."""
    doc_a: str = Field(default="Master_Services_Agreement_2021.md", description="Base contract filename")
    doc_b: str = Field(default="Amendment_No_2_2024.md", description="Amendment / SOW filename")
    tenant_id: str = Field(default="legal_contracts", description="Tenant data room partition")
    doc_a_text: Optional[str] = Field(default=None, description="Direct text for doc A (optional)")
    doc_b_text: Optional[str] = Field(default=None, description="Direct text for doc B (optional)")


class ContradictionResponse(BaseModel):
    """Structured response containing contradiction diff matrix."""
    doc_a: str
    doc_b: str
    summary: str
    overall_risk: str
    conflicts_count: int
    modifications_count: int
    consistent_count: Optional[int] = 0
    matrix: List[Dict[str, Any]]


@router.post("/analyze", response_model=ContradictionResponse)
async def analyze_contradictions(
    payload: ContradictionRequest,
    x_axiom_provider: Optional[str] = Header("gemini", alias="X-Axiom-Provider"),
) -> ContradictionResponse:
    """Analyze two contracts or amendments with the SCORE reasoning engine to detect contradictions."""
    result = analyze_contract_contradiction(
        doc_a_name=payload.doc_a,
        doc_b_name=payload.doc_b,
        tenant_id=payload.tenant_id,
        doc_a_text=payload.doc_a_text,
        doc_b_text=payload.doc_b_text,
        provider=x_axiom_provider or "gemini",
    )
    return ContradictionResponse(**result)


@router.get("/demo-pairs")
async def get_demo_contract_pairs() -> Dict[str, Any]:
    """Retrieve pre-configured M&A contract and amendment pairs for quick demonstration."""
    return {
        "doc_a": {
            "filename": "Master_Services_Agreement_2021.md",
            "title": "Master Services Agreement (Base Contract - March 2021)",
            "content": DEMO_CONTRACT_A,
        },
        "doc_b": {
            "filename": "Amendment_No_2_2024.md",
            "title": "Amendment No. 2 to Master Services Agreement (January 2024)",
            "content": DEMO_CONTRACT_B,
        },
    }
