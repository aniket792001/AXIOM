"""Automated Golden Evaluation Benchmark Runner for Axiom & SCORE.

Benchmarks the engine across high-stakes contractual failure modes:
1. Amendment Traps (superseding terms)
2. Multi-hop Appendix Disconnects
3. Table & Footnote Disclosures
4. Silent Bluff Prevention (Epistemic Humility)
"""

import json
from pathlib import Path
import time
from typing import Any, Dict, List

from axiom.core.graph import create_score_graph
from axiom.core.state import AgentState, DocumentChunk
from axiom.services.vector_store import get_vector_store

GOLDEN_DATASET_PATH = Path(__file__).parent / "golden_contracts.json"


def run_benchmark() -> Dict[str, Any]:
    """Execute evaluation benchmark across all golden test cases."""
    import os
    import sys
    from axiom.config.settings import get_settings

    if "--local" in sys.argv:
        os.environ["GEMINI_API_KEY"] = ""
        os.environ["OPENAI_API_KEY"] = ""
        get_settings.cache_clear()

    print("=" * 80)
    print("AXIOM & SCORE ENGINE: GOLDEN CONTRACT EVALUATION BENCHMARK")
    print("=" * 80)

    if not GOLDEN_DATASET_PATH.exists():
        raise FileNotFoundError(f"Benchmark dataset missing at {GOLDEN_DATASET_PATH}")

    with open(GOLDEN_DATASET_PATH, "r", encoding="utf-8-sig") as f:
        test_cases = json.load(f)

    store = get_vector_store()
    graph = create_score_graph()

    results: List[Dict[str, Any]] = []
    passed_count = 0
    total_latency = 0.0

    for idx, tc in enumerate(test_cases, 1):
        tc_id = tc["id"]
        tc_name = tc["name"]
        query = tc["query"]
        expected_facts = tc.get("expected_key_facts", [])
        forbidden = tc.get("forbidden_hallucinations", [])
        tenant_id = f"eval_{tc_id}"

        # 1. Ingest test documents for isolated evaluation tenant
        docs = [
            DocumentChunk(
                id=f"{tenant_id}:{d['id']}",
                content=d["content"],
                metadata=d.get("metadata", {}),
            )
            for d in tc.get("documents", [])
        ]
        store.ingest_documents(tenant_id, docs)

        # 2. Build Agent State & Invoke SCORE Engine
        initial_state: AgentState = {
            "tenant_id": tenant_id,
            "user_id": "eval_runner",
            "query": query,
            "rewritten_query": None,
            "route": "vector_store",
            "documents": docs,
            "graded_documents": [],
            "generation": "",
            "citations": [],
            "hallucination_status": "pending",
            "relevance_status": "pending",
            "loop_count": 0,
            "fallback_reason": None,
            "reasoning_trace": [],
        }

        start_time = time.perf_counter()
        final_state = graph.invoke(initial_state)
        elapsed = time.perf_counter() - start_time
        total_latency += elapsed

        generation = final_state.get("generation", "")
        hallucination_status = final_state.get("hallucination_status", "")
        citations = final_state.get("citations", [])

        # 3. Automated Scoring
        # Metric A: Factual Grounding (Must be grounded)
        is_grounded = hallucination_status == "grounded"

        # Metric B: Hallucination Check (Must not contain forbidden assertions)
        no_forbidden = not any(f.lower() in generation.lower() for f in forbidden)

        # Metric C: Fact Coverage (Did it include superseding facts or honest refusal?)
        facts_found = [fact for fact in expected_facts if fact.lower() in generation.lower()]
        fact_coverage = len(facts_found) / max(len(expected_facts), 1)

        # Pass criteria: Grounded + No forbidden hallucinations + At least partial key facts
        tc_passed = is_grounded and no_forbidden and (fact_coverage > 0 or len(citations) > 0)
        if tc_passed:
            passed_count += 1

        results.append({
            "id": tc_id,
            "name": tc_name,
            "passed": tc_passed,
            "is_grounded": is_grounded,
            "no_forbidden": no_forbidden,
            "fact_coverage": round(fact_coverage * 100, 1),
            "citations_count": len(citations),
            "latency_ms": round(elapsed * 1000, 1),
            "generation_snippet": generation[:120].replace("\n", " "),
        })

    # Summary Display
    print(f"\n{'Test Case':<42} | {'Verdict':<8} | {'Grounded':<8} | {'Coverage':<8} | {'Latency':<9}")
    print("-" * 80)
    for r in results:
        verdict = "PASSED" if r["passed"] else "FAILED"
        grounded_str = "YES" if r["is_grounded"] else "NO"
        cov_str = f"{r['fact_coverage']}%"
        lat_str = f"{r['latency_ms']}ms"
        print(f"{r['name'][:42]:<42} | {verdict:<8} | {grounded_str:<8} | {cov_str:<8} | {lat_str:<9}")

    success_rate = (passed_count / len(test_cases)) * 100
    avg_latency = (total_latency / len(test_cases)) * 1000

    print("=" * 80)
    print(f"BENCHMARK SUMMARY: {passed_count}/{len(test_cases)} Passed ({success_rate:.1f}%) | Avg Latency: {avg_latency:.1f}ms")
    print("=" * 80)

    return {
        "success_rate": success_rate,
        "passed_count": passed_count,
        "total_count": len(test_cases),
        "avg_latency_ms": avg_latency,
        "results": results,
    }


if __name__ == "__main__":
    benchmark_results = run_benchmark()
    if benchmark_results["success_rate"] < 75.0:
        exit(1)

