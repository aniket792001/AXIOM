"""Axiom & SCORE Engine: LangGraph State Machine.

Assembles the cyclical 9-node state machine with conditional routing,
relevance filtering, self-correction loops, and hallucination audits.
"""

from typing import Any, Literal, Optional
from langgraph.graph import END, StateGraph

from axiom.config.settings import get_settings
from axiom.core.nodes import (
    fallback_node,
    generator_node,
    grader_node,
    hallucination_grader_node,
    retriever_node,
    rewriter_node,
    router_node,
)
from axiom.core.state import AgentState


def decide_route(state: AgentState) -> Literal["retriever", "generator"]:
    """Conditional edge from router node."""
    route = state.get("route", "vector_store")
    if route == "direct":
        return "generator"
    return "retriever"


def decide_after_grading(state: AgentState) -> Literal["generator", "rewriter", "fallback"]:
    """Conditional edge from document grader node.

    Determines whether context is sufficient for generation,
    requires query expansion, or triggers a graceful fallback.
    """
    settings = get_settings()
    graded_docs = state.get("graded_documents", [])
    loop_count = state.get("loop_count", 0)

    if graded_docs:
        return "generator"

    # Context insufficient: Check loop ceiling
    if loop_count >= settings.max_loop_count:
        return "fallback"

    return "rewriter"


def decide_after_hallucination(state: AgentState) -> Literal["end", "generator", "fallback"]:
    """Conditional edge from hallucination grader node.

    Ensures 100% grounded answers before releasing to the user.
    """
    settings = get_settings()
    status = state.get("hallucination_status", "grounded")
    loop_count = state.get("loop_count", 0)

    if status == "grounded":
        return "end"

    if loop_count >= settings.max_loop_count:
        return "fallback"

    return "generator"


def create_score_graph(checkpointer: Optional[Any] = None) -> Any:
    """Build and compile the SCORE LangGraph state machine.

    Args:
        checkpointer: Optional persistent checkpointer (e.g., RedisSaver or PostgresSaver).

    Returns:
        Compiled LangGraph executable workflow.
    """
    workflow = StateGraph(AgentState)

    # 1. Register Nodes
    workflow.add_node("router", router_node)
    workflow.add_node("retriever", retriever_node)
    workflow.add_node("grader", grader_node)
    workflow.add_node("rewriter", rewriter_node)
    workflow.add_node("generator", generator_node)
    workflow.add_node("hallucination_grader", hallucination_grader_node)
    workflow.add_node("fallback", fallback_node)

    # 2. Define Entry Point
    workflow.set_entry_point("router")

    # 3. Add Routing Edges
    workflow.add_conditional_edges(
        "router",
        decide_route,
        {
            "retriever": "retriever",
            "generator": "generator",
        },
    )

    # Retrieval -> Grading
    workflow.add_edge("retriever", "grader")

    # Grading -> (Generator | Rewriter | Fallback)
    workflow.add_conditional_edges(
        "grader",
        decide_after_grading,
        {
            "generator": "generator",
            "rewriter": "rewriter",
            "fallback": "fallback",
        },
    )

    # Rewriter -> Re-retrieve (Cyclical Loop!)
    workflow.add_edge("rewriter", "retriever")

    # Generator -> Hallucination Audit
    workflow.add_edge("generator", "hallucination_grader")

    # Hallucination Audit -> (END | Re-generate | Fallback)
    workflow.add_conditional_edges(
        "hallucination_grader",
        decide_after_hallucination,
        {
            "end": END,
            "generator": "generator",
            "fallback": "fallback",
        },
    )

    # Fallback -> END
    workflow.add_edge("fallback", END)

    return workflow.compile(checkpointer=checkpointer)
