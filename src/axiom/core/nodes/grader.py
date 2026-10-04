"""Document Grader Node for Axiom & SCORE Engine.

Evaluates retrieved chunks for relevance to the user query.
Filters out noisy, irrelevant context before generation.
"""

from typing import Any, Dict, List
from pydantic import BaseModel, Field

from axiom.config.settings import get_settings
from axiom.core.prompts_loader import load_prompt
from axiom.core.state import AgentState, DocumentChunk, StepEvent


class GradeResult(BaseModel):
    """Structured relevance evaluation for a single document snippet."""
    binary_score: str = Field(description="'yes' if relevant, 'no' if irrelevant")
    reasoning: str = Field(default="", description="Brief evaluation reasoning")


def grader_node(state: AgentState) -> Dict[str, Any]:
    """Grade each retrieved chunk for relevance, discarding irrelevant noise."""
    settings = get_settings()
    query = state.get("rewritten_query") or state.get("query", "")
    documents = state.get("documents", [])

    graded_chunks: List[DocumentChunk] = []
    discarded_count = 0

    from axiom.config.quota import is_provider_available, report_quota_exhausted

    llm = None
    try:
        if settings.gemini_api_key and is_provider_available("gemini"):
            from langchain_google_genai import ChatGoogleGenerativeAI
            llm = ChatGoogleGenerativeAI(
                model=settings.fast_model,
                google_api_key=settings.gemini_api_key,
                temperature=0.0,
                max_retries=0,
                request_timeout=10.0,
            ).with_structured_output(GradeResult)
        elif settings.openai_api_key and is_provider_available("openai"):
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(
                model=settings.fast_model,
                api_key=settings.openai_api_key,
                temperature=0.0,
            ).with_structured_output(GradeResult)
    except Exception as exc:
        if "RESOURCE_EXHAUSTED" in str(exc) or "429" in str(exc):
            report_quota_exhausted("gemini", 120.0)
        llm = None

    for doc in documents:
        score = "yes"
        if llm:
            try:
                prompt = load_prompt("grader", query=query, chunk_id=doc.id, content=doc.content)
                result: GradeResult = llm.invoke(prompt)
                score = result.binary_score.lower().strip()
            except Exception as exc:
                if "RESOURCE_EXHAUSTED" in str(exc) or "429" in str(exc):
                    report_quota_exhausted("gemini", 120.0)
                # Fallback on LLM network exception: use keyword overlap
                query_words = set(w.strip("?.,!") for w in query.lower().split() if len(w) > 2)
                content_words = set(w.strip("?.,!") for w in doc.content.lower().split() if len(w) > 2)
                overlap = query_words.intersection(content_words)
                score = "yes" if len(overlap) >= 1 else "no"
        else:
            # Deterministic heuristic grading in key-free test mode
            query_words = set(w.strip("?.,!") for w in query.lower().split() if len(w) > 2)
            content_words = set(w.strip("?.,!") for w in doc.content.lower().split() if len(w) > 2)
            overlap = query_words.intersection(content_words)
            score = "yes" if len(overlap) >= 1 else "no"

        if score == "yes":
            doc.relevance_score = 1.0
            graded_chunks.append(doc)
        else:
            discarded_count += 1

    event = StepEvent(
        node="grader",
        status="completed",
        details={
            "retained": str(len(graded_chunks)),
            "discarded": str(discarded_count),
        },
    )

    return {
        "graded_documents": graded_chunks,
        "reasoning_trace": [event],
    }
