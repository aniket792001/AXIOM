"""Integration tests for Cryptographic PDF, Excel and Audit Verification API."""

import pytest
from fastapi.testclient import TestClient
from axiom.api.main import app
from axiom.services.report_export_service import prepare_audit_metadata

client = TestClient(app)


def test_export_pdf_certificate():
    """Verify endpoint generates valid binary PDF with PDF magic header."""
    payload = {
        "query": "What is the liability cap under Section 9.1?",
        "generation": "The aggregate liability under Section 9.1 is strictly capped at $500,000.",
        "citations": [
            {
                "source_document": "Master_Services_Agreement_2021.md",
                "page": 3,
                "relevance_score": 0.98,
                "chunk_id": "chunk_sec_9_1",
                "excerpt": "Total aggregate liability of either party shall not exceed five hundred thousand dollars ($500,000).",
            }
        ],
        "tenant_id": "legal_contracts",
        "session_id": "test_session_pdf",
        "hallucination_status": "grounded",
        "format": "pdf",
    }
    response = client.post("/api/v1/export/pdf", json=payload)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    # PDF specification magic byte header
    assert response.content.startswith(b"%PDF-")
    assert len(response.content) > 1000


def test_export_excel_certificate():
    """Verify endpoint generates valid binary Excel workbook with PK zip magic header."""
    payload = {
        "query": "What is the dispute resolution forum in Clause 14?",
        "generation": "Disputes are subject to the exclusive jurisdiction of the state courts of Delaware.",
        "citations": [
            {
                "source_document": "Master_Services_Agreement_2021.md",
                "page": 5,
                "relevance_score": 0.95,
                "chunk_id": "chunk_sec_14",
                "excerpt": "Any dispute arising hereunder shall be brought exclusively in the state courts of Delaware.",
            }
        ],
        "tenant_id": "legal_contracts",
        "session_id": "test_session_xlsx",
        "hallucination_status": "grounded",
        "format": "excel",
    }
    response = client.post("/api/v1/export/excel", json=payload)
    assert response.status_code == 200
    assert "spreadsheetml.sheet" in response.headers["content-type"]
    # OpenXML zip format magic bytes (PK\x03\x04)
    assert response.content.startswith(b"PK")
    assert len(response.content) > 2000


def test_verify_certificate_signature_valid_and_tampered():
    """Verify cryptographic HMAC-SHA256 signature verification passes on valid and fails on tampered data."""
    meta = prepare_audit_metadata(
        query="What is the payment term?",
        generation="Payment is Net 30 calendar days.",
        citations=[{"excerpt": "Invoices payable within thirty (30) days."}],
        tenant_id="legal_contracts",
        session_id="session_verify_1",
    )

    # 1. Valid Signature Verification
    verify_payload = {
        "certificate_id": meta["certificate_id"],
        "query": meta["query"],
        "generation": meta["generation"],
        "citations": meta["citations"],
        "timestamp": meta["issued_at"],
        "signature": meta["signature"],
    }
    res_valid = client.post("/api/v1/export/verify", json=verify_payload)
    assert res_valid.status_code == 200
    data_valid = res_valid.json()
    assert data_valid["verified"] is True
    assert data_valid["status"] == "VALID_TAMPER_EVIDENT"

    # 2. Tampered Query (Attacker changed query text)
    tampered_payload = dict(verify_payload)
    tampered_payload["query"] = "Attacker modified question to alter evidence!"
    res_tampered = client.post("/api/v1/export/verify", json=tampered_payload)
    assert res_tampered.status_code == 200
    data_tampered = res_tampered.json()
    assert data_tampered["verified"] is False
    assert data_tampered["status"] == "INVALID_OR_TAMPERED"
