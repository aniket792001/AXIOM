"""Unit tests for Axiom & SCORE LangGraph State Machine."""

import pytest
from axiom.core.graph import create_score_graph
from axiom.core.state import AgentState, DocumentChunk


def test_graph_compilation():
    """Verify that the state graph compiles without errors."""
    graph = create_score_graph()
    assert graph is not None


def test_graph_end_to_end_grounded_execution():
    """Test standard execution flow with verified grounding."""
    graph = create_score_graph()

    initial_state: AgentState = {
        "tenant_id": "tenant_enterprise_01",
        "user_id": "user_analyst_99",
        "query": "What is the liability cap for Tier 2 enterprise customers?",
        "rewritten_query": None,
        "route": "vector_store",
        "documents": [
            DocumentChunk(
                id="doc_msa:chunk_1",
                content="Under the 2024 Addendum, the liability cap for Tier 2 enterprise is $2,500,000.",
                metadata={"file": "Addendum.pdf"},
            )
        ],
        "graded_documents": [],
        "generation": "",
        "citations": [],
        "hallucination_status": "pending",
        "relevance_status": "pending",
        "loop_count": 0,
        "fallback_reason": None,
        "reasoning_trace": [],
    }

    result = graph.invoke(initial_state)

    assert result["generation"] != ""
    assert result["hallucination_status"] == "grounded"
    assert len(result["reasoning_trace"]) >= 4

    # Ensure router, retriever, grader, generator, and hallucination_grader all logged traces
    nodes_executed = [event.node for event in result["reasoning_trace"]]
    assert "router" in nodes_executed
    assert "grader" in nodes_executed
    assert "generator" in nodes_executed
    assert "hallucination_grader" in nodes_executed


def test_graph_loop_ceiling_and_fallback():
    """Verify that the engine gracefully routes to fallback when loop ceiling is reached."""
    graph = create_score_graph()

    # State with 0 documents and loop_count already at maximum (3)
    exhausted_state: AgentState = {
        "tenant_id": "tenant_enterprise_01",
        "user_id": "user_analyst_99",
        "query": "Non-existent clause XYZ?",
        "rewritten_query": "Non-existent clause XYZ?",
        "route": "vector_store",
        "documents": [],
        "graded_documents": [],
        "generation": "",
        "citations": [],
        "hallucination_status": "pending",
        "relevance_status": "pending",
        "loop_count": 3,  # Reached max loop ceiling
        "fallback_reason": None,
        "reasoning_trace": [],
    }

    result = graph.invoke(exhausted_state)

    assert result["fallback_reason"] == "loop_ceiling_exhausted"
    assert "Unable to provide a verified answer" in result["generation"]
