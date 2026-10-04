"""Chat & Real-Time SSE Query Routes for Axiom API Gateway."""

import asyncio
import json
from typing import Any, AsyncGenerator, Dict
from fastapi import APIRouter, HTTPException, status
from sse_starlette.sse import EventSourceResponse

from axiom.api.schemas.query import QueryRequest, QueryResponse
from axiom.core.graph import create_score_graph
from axiom.core.state import AgentState

router = APIRouter(prefix="/api/v1", tags=["Query & Streaming"])


def _build_initial_state(payload: QueryRequest) -> AgentState:
    """Construct a clean initial AgentState from the incoming request."""
    return {
        "tenant_id": payload.tenant_id,
        "user_id": payload.user_id or "anonymous_user",
        "query": payload.query,
        "rewritten_query": None,
        "route": "vector_store",
        "documents": [],
        "graded_documents": [],
        "generation": "",
        "citations": [],
        "hallucination_status": "pending",
        "relevance_status": "pending",
        "loop_count": 0,
        "fallback_reason": None,
        "reasoning_trace": [],
    }


@router.post("/query", response_model=QueryResponse)
async def query_synchronous(payload: QueryRequest) -> QueryResponse:
    """Execute a synchronous reasoning query over Axiom's SCORE engine."""
    graph = create_score_graph()
    initial_state = _build_initial_state(payload)

    try:
        final_state = graph.invoke(initial_state)
        return QueryResponse(
            query=payload.query,
            generation=final_state.get("generation", ""),
            citations=final_state.get("citations", []),
            hallucination_status=final_state.get("hallucination_status", "grounded"),
            fallback_reason=final_state.get("fallback_reason"),
            reasoning_trace=final_state.get("reasoning_trace", []),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Engine execution error: {str(exc)}",
        )


@router.post("/query/stream")
async def query_streaming(payload: QueryRequest) -> EventSourceResponse:
    """Stream real-time agent execution events and final answer via Server-Sent Events (SSE)."""
    graph = create_score_graph()
    initial_state = _build_initial_state(payload)

    async def sse_event_stream() -> AsyncGenerator[Dict[str, Any], None]:
        # 1. Initial Start Event
        yield {
            "event": "status",
            "data": json.dumps({
                "phase": "initialized",
                "query": payload.query,
                "tenant_id": payload.tenant_id,
            }),
        }
        await asyncio.sleep(0.01)

        try:
            # 2. Stream LangGraph node transitions asynchronously
            async for update in graph.astream(initial_state, stream_mode="updates"):
                for node_name, node_output in update.items():
                    # Extract last step event details if available
                    details: Dict[str, Any] = {}
                    if "reasoning_trace" in node_output and node_output["reasoning_trace"]:
                        last_event = node_output["reasoning_trace"][-1]
                        details = last_event.details if hasattr(last_event, "details") else {}

                    yield {
                        "event": "status",
                        "data": json.dumps({
                            "node": node_name,
                            "details": details,
                        }),
                    }
                    await asyncio.sleep(0.01)

                    # Stream answer when generator finishes
                    if node_name == "generator" and "generation" in node_output:
                        citations_list = [
                            c.model_dump() if hasattr(c, "model_dump") else dict(c)
                            for c in node_output.get("citations", [])
                        ]
                        yield {
                            "event": "answer",
                            "data": json.dumps({
                                "generation": node_output["generation"],
                                "citations": citations_list,
                            }),
                        }
                        await asyncio.sleep(0.01)

                    # Stream refusal when fallback executes
                    if node_name == "fallback" and "generation" in node_output:
                        yield {
                            "event": "fallback",
                            "data": json.dumps({
                                "generation": node_output["generation"],
                                "reason": node_output.get("fallback_reason", "loop_ceiling_exhausted"),
                            }),
                        }
                        await asyncio.sleep(0.01)

            # 3. Stream Completion Event
            yield {
                "event": "done",
                "data": json.dumps({"status": "completed"}),
            }
            await asyncio.sleep(0.01)
        except Exception as exc:
            yield {
                "event": "error",
                "data": json.dumps({"error": str(exc)}),
            }

    return EventSourceResponse(sse_event_stream())
