"""Router Node for Axiom & SCORE Engine.

Classifies incoming query intent to determine whether to route to
the internal vector store (enterprise docs) or live web search.
"""

import json
from typing import Any, Dict
from pydantic import BaseModel, Field

from axiom.config.settings import get_settings
from axiom.core.prompts_loader import load_prompt
from axiom.core.state import AgentState, StepEvent


import re


class RouteDecision(BaseModel):
    """Structured decision output for the router node."""
    route: str = Field(description="Selected route: vector_store, web_search, or direct")
    reasoning: str = Field(description="Brief explanation of routing choice")


def _classify_heuristic(query: str) -> RouteDecision:
    lowered = query.lower().strip()
    words = set(re.findall(r"\b[a-zA-Z]+\b", lowered))
    if words.intersection({"hi", "hello", "hey", "greetings"}) or lowered in ["who are you", "who are you?"]:
        # Only treat as direct greeting if query is very short or purely a greeting
        if len(words) <= 4:
            return RouteDecision(route="direct", reasoning="Heuristic detected conversational greeting")

    realtime_terms = ["latest news", "today news", "current weather", "stock price", "live market"]
    if any(t in lowered for t in realtime_terms):
        return RouteDecision(route="web_search", reasoning="Heuristic detected real-time keywords")

    return RouteDecision(route="vector_store", reasoning="Heuristic routed to enterprise documents")



def router_node(state: AgentState) -> Dict[str, Any]:
    """Analyze the query and decide the appropriate retrieval channel."""
    settings = get_settings()
    query = state.get("query", "")
    
    prompt = load_prompt("router", query=query)
    decision = RouteDecision(route="vector_store", reasoning="Default enterprise retrieval")

    from axiom.config.quota import is_provider_available, report_quota_exhausted

    # If Gemini or OpenAI API keys are available, invoke structured LLM
    try:
        if settings.gemini_api_key and is_provider_available("gemini"):
            from langchain_google_genai import ChatGoogleGenerativeAI
            llm = ChatGoogleGenerativeAI(
                model=settings.fast_model,
                google_api_key=settings.gemini_api_key,
                temperature=0.0,
                max_retries=0,
                request_timeout=10.0,
            )
            structured_llm = llm.with_structured_output(RouteDecision)
            decision = structured_llm.invoke(prompt)
        elif settings.openai_api_key and is_provider_available("openai"):
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(
                model=settings.fast_model,
                api_key=settings.openai_api_key,
                temperature=0.0,
            )
            structured_llm = llm.with_structured_output(RouteDecision)
            decision = structured_llm.invoke(prompt)
        else:
            decision = _classify_heuristic(query)
    except Exception as exc:
        report_quota_exhausted("gemini", 300.0)
        decision = _classify_heuristic(query)

    event = StepEvent(
        node="router",
        status="completed",
        details={"route": decision.route, "reasoning": decision.reasoning},
    )

    return {
        "route": decision.route,
        "reasoning_trace": [event],
    }
