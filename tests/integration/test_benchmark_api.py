"""Integration tests for Live RAGAS Evaluation & Quality Benchmark API."""

import pytest
from fastapi.testclient import TestClient
from axiom.api.main import app

client = TestClient(app)


def test_get_benchmark_summary():
    """Verify endpoint returns complete benchmark summary and comparative metrics."""
    response = client.get("/api/v1/benchmark/summary")
    assert response.status_code == 200
    data = response.json()

    assert "overall_pass_rate" in data
    assert data["overall_pass_rate"] >= 75.0
    assert "ragas_metrics" in data
    assert "faithfulness" in data["ragas_metrics"]
    assert data["ragas_metrics"]["faithfulness"] >= 0.90
    assert "epistemic_humility" in data["ragas_metrics"]

    assert "comparative_baselines" in data
    assert len(data["comparative_baselines"]) >= 4

    assert "results" in data
    assert len(data["results"]) >= 4
    for r in data["results"]:
        assert "name" in r
        assert "passed" in r
        assert "is_grounded" in r
        assert "latency_ms" in r


def test_get_benchmark_test_cases():
    """Verify endpoint provides definitions of golden benchmark test cases."""
    response = client.get("/api/v1/benchmark/cases")
    assert response.status_code == 200
    cases = response.json()
    assert isinstance(cases, list)
    assert len(cases) >= 4
    case_ids = [c["id"] for c in cases]
    assert "eval_001_amendment_trap" in case_ids
    assert "eval_004_silent_bluff_refusal" in case_ids


def test_run_benchmark_live():
    """Verify on-demand execution of golden contract benchmark suite."""
    response = client.post("/api/v1/benchmark/run")
    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] >= 4
    assert "results" in data
