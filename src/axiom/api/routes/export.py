"""Audit Certificate Export Routes for Axiom API Gateway.

Provides enterprise-ready export capabilities for Cryptographic PDF Audit Certificates,
multi-sheet Excel workbooks, and real-time cryptographic signature verification.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Response, status
from pydantic import BaseModel, Field

from axiom.services.audit_exporter import generate_audit_certificate
from axiom.services.report_export_service import (
    generate_excel_audit_workbook,
    generate_pdf_audit_certificate,
    prepare_audit_metadata,
    verify_audit_certificate,
)

router = APIRouter(prefix="/api/v1/export", tags=["Audit & Governance"])


class CertificateRequest(BaseModel):
    """Payload to generate a Grounded Audit Certificate or Report."""
    query: str = Field(..., description="The original query")
    generation: str = Field(..., description="The synthesized response")
    citations: List[Dict[str, Any]] = Field(default_factory=list, description="Verified citations")
    reasoning_trace: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    tenant_id: str = Field(default="default_tenant")
    session_id: str = Field(default="default_session")
    hallucination_status: str = Field(default="grounded")
    format: str = Field(default="markdown", description="'markdown', 'pdf', 'excel', or 'json'")


class VerifyCertificateRequest(BaseModel):
    """Payload to verify the cryptographic authenticity of an exported certificate."""
    certificate_id: str
    query: str
    generation: str
    citations: List[Dict[str, Any]] = Field(default_factory=list)
    timestamp: str
    signature: str


@router.post("/certificate", status_code=status.HTTP_200_OK)
async def export_certificate(payload: CertificateRequest) -> Any:
    """Generate and return a cryptographic Grounding Audit Certificate in Markdown, JSON, PDF, or Excel."""
    fmt = payload.format.lower()

    if fmt == "pdf":
        return await export_pdf_certificate(payload)
    elif fmt in ["excel", "xlsx"]:
        return await export_excel_certificate(payload)

    cert = generate_audit_certificate(
        query=payload.query,
        generation=payload.generation,
        citations=payload.citations,
        reasoning_trace=payload.reasoning_trace,
        tenant_id=payload.tenant_id,
        session_id=payload.session_id,
        hallucination_status=payload.hallucination_status,
    )

    if fmt == "markdown":
        headers = {
            "Content-Disposition": f'attachment; filename="{cert["certificate_id"]}.md"',
        }
        return Response(
            content=cert["markdown_content"],
            media_type="text/markdown",
            headers=headers,
        )

    return cert


@router.post("/pdf", status_code=status.HTTP_200_OK)
async def export_pdf_certificate(payload: CertificateRequest) -> Response:
    """Generate and download a Cryptographic PDF Audit Certificate."""
    meta = prepare_audit_metadata(
        query=payload.query,
        generation=payload.generation,
        citations=payload.citations,
        reasoning_trace=payload.reasoning_trace,
        tenant_id=payload.tenant_id,
        session_id=payload.session_id,
        hallucination_status=payload.hallucination_status,
    )
    pdf_bytes = generate_pdf_audit_certificate(meta)
    headers = {
        "Content-Disposition": f'attachment; filename="{meta["certificate_id"]}.pdf"',
    }
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers=headers,
    )


@router.post("/excel", status_code=status.HTTP_200_OK)
async def export_excel_certificate(payload: CertificateRequest) -> Response:
    """Generate and download a Multi-Tab Excel (.xlsx) Audit Workbook."""
    meta = prepare_audit_metadata(
        query=payload.query,
        generation=payload.generation,
        citations=payload.citations,
        reasoning_trace=payload.reasoning_trace,
        tenant_id=payload.tenant_id,
        session_id=payload.session_id,
        hallucination_status=payload.hallucination_status,
    )
    excel_bytes = generate_excel_audit_workbook(meta)
    headers = {
        "Content-Disposition": f'attachment; filename="{meta["certificate_id"]}.xlsx"',
    }
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )


@router.post("/verify", status_code=status.HTTP_200_OK)
async def verify_certificate_endpoint(payload: VerifyCertificateRequest) -> Dict[str, Any]:
    """Verify the cryptographic HMAC-SHA256 signature and tamper-evidence of an audit report."""
    result = verify_audit_certificate(
        cert_id=payload.certificate_id,
        query=payload.query,
        generation=payload.generation,
        citations=payload.citations,
        timestamp=payload.timestamp,
        provided_signature=payload.signature,
    )
    return result
