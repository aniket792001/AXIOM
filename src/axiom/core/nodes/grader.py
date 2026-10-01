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

    llm = None
    if settings.gemini_api_key:
        from langchain_google_genai import ChatGoogleGenerativeAI
        llm = ChatGoogleGenerativeAI(
            model=settings.fast_model,
            google_api_key=settings.gemini_api_key,
            temperature=0.0,
        ).with_structured_output(GradeResult)
    elif settings.openai_api_key:
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(
            model=settings.fast_model,
            api_key=settings.openai_api_key,
            temperature=0.0,
        ).with_structured_output(GradeResult)

    for doc in documents:
        score = "yes"
        if llm:
            try:
                prompt = load_prompt("grader", query=query, chunk_id=doc.id, content=doc.content)
                result: GradeResult = llm.invoke(prompt)
                score = result.binary_score.lower().strip()
            except Exception:
                score = "yes"  # Fallback: retain on grading exception
        else:
            # Deterministic heuristic grading in key-free test mode
            query_words = set(query.lower().split())
            content_words = set(doc.content.lower().split())
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
