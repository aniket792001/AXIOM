"""Query Rewriter Node for Axiom & SCORE Engine.

Reformulates and expands search queries when retrieved context
is insufficient, missing superseding amendments, or lacking definitions.
"""

from typing import Any, Dict
from pydantic import BaseModel, Field

from axiom.config.settings import get_settings
from axiom.core.prompts_loader import load_prompt
from axiom.core.state import AgentState, StepEvent


class RewriteOutput(BaseModel):
    """Structured output for the query rewriter node."""
    rewritten_query: str = Field(description="Optimized semantic search query")
    search_strategy: str = Field(default="", description="Strategy behind reformulation")


def rewriter_node(state: AgentState) -> Dict[str, Any]:
    """Expand and rewrite the query to target missing contractual/factual clauses."""
    settings = get_settings()
    original_query = state.get("query", "")
    current_loop = state.get("loop_count", 0) + 1
    previous_query = state.get("rewritten_query") or original_query

    prompt = load_prompt(
        "rewriter",
        query=original_query,
        loop_count=str(current_loop),
        previous_query=previous_query,
        feedback="Context lacked complete clauses or required superseding addendums.",
    )

    new_query = f"{original_query} addendum amendment"
    strategy = "Keyword expansion fallback"

    try:
        if settings.gemini_api_key:
            from langchain_google_genai import ChatGoogleGenerativeAI
            llm = ChatGoogleGenerativeAI(
                model=settings.fast_model,
                google_api_key=settings.gemini_api_key,
                temperature=0.0,
            ).with_structured_output(RewriteOutput)
            result = llm.invoke(prompt)
            new_query = result.rewritten_query
            strategy = result.search_strategy
        elif settings.openai_api_key:
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(
                model=settings.fast_model,
                api_key=settings.openai_api_key,
                temperature=0.0,
            ).with_structured_output(RewriteOutput)
            result = llm.invoke(prompt)
            new_query = result.rewritten_query
            strategy = result.search_strategy
    except Exception:
        new_query = f"{original_query} addendum amendment"

    event = StepEvent(
        node="rewriter",
        status="completed",
        details={
            "attempt": str(current_loop),
            "new_query": new_query,
            "strategy": strategy,
        },
    )

    return {
        "rewritten_query": new_query,
        "loop_count": current_loop,
        "reasoning_trace": [event],
    }
