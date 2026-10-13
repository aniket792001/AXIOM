"""Integration tests for Contract Contradiction & Diff Matrix API."""

import pytest
from fastapi.testclient import TestClient
from axiom.api.main import app

client = TestClient(app)


def test_get_demo_contract_pairs():
    """Verify endpoint provides pre-seeded M&A contract and amendment pair."""
    response = client.get("/api/v1/contradiction/demo-pairs")
    assert response.status_code == 200
    data = response.json()
    assert "doc_a" in data and "doc_b" in data
    assert "Master_Services_Agreement" in data["doc_a"]["filename"]
    assert "Amendment_No_2" in data["doc_b"]["filename"]
    assert len(data["doc_a"]["content"]) > 100
    assert len(data["doc_b"]["content"]) > 100


def test_analyze_contract_contradictions_demo():
    """Verify contradiction analysis on demo contracts identifies high-risk contradictions."""
    payload = {
        "doc_a": "Master_Services_Agreement_2021.md",
        "doc_b": "Amendment_No_2_2024.md",
        "tenant_id": "legal_contracts",
    }
    response = client.post("/api/v1/contradiction/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["doc_a"] == "Master_Services_Agreement_2021.md"
    assert data["doc_b"] == "Amendment_No_2_2024.md"
    assert data["overall_risk"] in ["HIGH", "MEDIUM", "LOW"]
    assert data["conflicts_count"] >= 1
    assert len(data["matrix"]) >= 3

    # Check structure of matrix entries
    first_item = data["matrix"][0]
    assert "category" in first_item
    assert "status" in first_item
    assert first_item["status"] in ["CONTRADICTION", "MODIFICATION", "CONSISTENT"]
    assert "risk_level" in first_item
    assert "doc_a_clause" in first_item
    assert "doc_b_clause" in first_item
    assert "analysis" in first_item
    assert "precedence_ruling" in first_item


def test_analyze_custom_contract_snippets():
    """Verify contradiction analysis handles direct text payloads."""
    payload = {
        "doc_a": "Custom_Agreement.txt",
        "doc_b": "Custom_Amendment.txt",
        "tenant_id": "legal_contracts",
        "doc_a_text": "Section 4. Governing Law: This Agreement shall be governed by Delaware law.",
        "doc_b_text": "Section 4. Governing Law: This Agreement and all disputes shall be governed by California law.",
    }
    response = client.post("/api/v1/contradiction/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "matrix" in data
    assert isinstance(data["matrix"], list)
