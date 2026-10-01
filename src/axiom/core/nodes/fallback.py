"""Fallback Handler Node for Axiom & SCORE Engine.

Emits transparent, diagnostic refusals when the 3-loop ceiling is reached
or verified factual context cannot be established.
Enforces the zero-hallucination mandate.
"""

from typing import Any, Dict
from axiom.core.state import AgentState, StepEvent


def fallback_node(state: AgentState) -> Dict[str, Any]:
    """Format an honest diagnostic refusal rather than hallucinating an answer."""
    query = state.get("query", "")
    loop_count = state.get("loop_count", 0)
    rewritten_query = state.get("rewritten_query", "None")

    refusal_text = (
        f"Unable to provide a verified answer with zero-hallucination certainty.\n\n"
        f"**Diagnostic Summary**:\n"
        f"- Original Query: \"{query}\"\n"
        f"- Reformulation Attempts: {loop_count} search iterations executed\n"
        f"- Last Query Tested: \"{rewritten_query}\"\n\n"
        f"**Reason**: The available enterprise knowledge base does not contain verified clauses, "
        f"addendums, or definitions matching this specific request. In adherence to Axiom's "
        f"Epistemic Humility principle, the system refuses to extrapolate or guess without explicit citations."
    )

    event = StepEvent(
        node="fallback",
        status="completed",
        details={
            "reason": "loop_ceiling_exhausted",
            "attempts": str(loop_count),
        },
    )

    return {
        "generation": refusal_text,
        "fallback_reason": "loop_ceiling_exhausted",
        "hallucination_status": "grounded",
        "reasoning_trace": [event],
    }
