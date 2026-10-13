"""Chat & Real-Time SSE Query Routes for Axiom API Gateway."""

import asyncio
from collections import defaultdict
import json
from typing import Any, AsyncGenerator, Dict, List
from fastapi import APIRouter, HTTPException, status
from sse_starlette.sse import EventSourceResponse

from datetime import datetime
from axiom.api.schemas.query import QueryRequest, QueryResponse
from axiom.core.graph import create_score_graph
from axiom.core.state import AgentState
from axiom.db.database import SessionLocal
from axiom.db.models import QueryRecord, SessionThread

router = APIRouter(prefix="/api/v1", tags=["Query & Streaming"])

# In-memory multi-turn session histories
_session_histories: Dict[str, List[Dict[str, str]]] = defaultdict(list)


def _persist_query_to_db(
    session_id: str,
    tenant_id: str,
    user_id: str,
    query: str,
    generation: str,
    citations: list = None,
    retrieved_chunks: list = None,
    hallucination_status: str = "grounded",
    loop_count: int = 0,
    rewritten_query: str = None,
    route: str = "vector_store",
) -> None:
    """Persist query execution, retrieval audit, and generation to SQLite."""
    try:
        with SessionLocal() as db:
            thread = db.query(SessionThread).filter_by(id=session_id).first()
            if not thread:
                title = query[:40] + ("..." if len(query) > 40 else "")
                thread = SessionThread(
                    id=session_id,
                    tenant_id=tenant_id,
                    user_id=user_id or "anonymous",
                    title=title,
                )
                db.add(thread)
            else:
                thread.updated_at = datetime.utcnow()

            citations_json = json.dumps([
                c.model_dump() if hasattr(c, "model_dump") else dict(c) for c in (citations or [])
            ])
            retrieved_chunks_json = json.dumps([
                c.model_dump() if hasattr(c, "model_dump") else dict(c) for c in (retrieved_chunks or [])
            ])

            record = QueryRecord(
                session_id=session_id,
                tenant_id=tenant_id,
                user_id=user_id or "anonymous",
                query=query,
                rewritten_query=rewritten_query,
                route=route,
                generation=generation,
                citations_json=citations_json,
                retrieved_chunks_json=retrieved_chunks_json,
                hallucination_status=hallucination_status,
                loop_count=loop_count,
            )
            db.add(record)
            db.commit()
    except Exception as exc:
        print(f"[!] Failed to persist query record to DB: {exc}")


def _build_initial_state(payload: QueryRequest) -> AgentState:
    """Construct a clean initial AgentState with conversational history."""
    session_id = payload.session_id or "default_session"
    history = list(_session_histories[session_id])
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
        "session_id": session_id,
        "chat_history": history,
    }


@router.get("/sessions")
async def list_sessions(tenant_id: str = "default_tenant", user_id: str = None) -> List[Dict[str, Any]]:
    """List customer conversation threads stored in the SQLite database."""
    with SessionLocal() as db:
        q = db.query(SessionThread).filter_by(tenant_id=tenant_id)
        if user_id:
            q = q.filter_by(user_id=user_id)
        threads = q.order_by(SessionThread.updated_at.desc()).limit(50).all()
        return [t.to_dict() for t in threads]


@router.get("/sessions/{session_id}/history")
async def get_session_history(session_id: str) -> List[Dict[str, Any]]:
    """Get complete conversation history and retrieval audit records for a session."""
    with SessionLocal() as db:
        records = db.query(QueryRecord).filter_by(session_id=session_id).order_by(QueryRecord.created_at.asc()).all()
        return [r.to_dict() for r in records]


@router.get("/history/audit")
async def get_history_audit(tenant_id: str = None, limit: int = 100) -> Dict[str, Any]:
    """Retrieve full audit log of customer queries, retrievals, and hallucination verdicts."""
    with SessionLocal() as db:
        q = db.query(QueryRecord)
        if tenant_id:
            q = q.filter_by(tenant_id=tenant_id)
        records = q.order_by(QueryRecord.created_at.desc()).limit(limit).all()
        return {
            "total": len(records),
            "records": [r.to_dict() for r in records],
        }


@router.delete("/sessions/{session_id}")
@router.delete("/session/{session_id}")
async def clear_session(session_id: str) -> dict:
    """Clear conversation history for a given session ID from memory and database."""
    _session_histories.pop(session_id, None)
    with SessionLocal() as db:
        db.query(QueryRecord).filter_by(session_id=session_id).delete()
        db.query(SessionThread).filter_by(id=session_id).delete()
        db.commit()
    return {"status": "success", "session_id": session_id, "message": "Conversation history cleared."}


@router.post("/query", response_model=QueryResponse)
async def query_synchronous(payload: QueryRequest) -> QueryResponse:
    """Execute a synchronous reasoning query over Axiom's SCORE engine."""
    graph = create_score_graph()
    initial_state = _build_initial_state(payload)

    try:
        final_state = graph.invoke(initial_state)
        gen = final_state.get("generation", "")
        session_id = payload.session_id or "default_session"
        if gen:
            _session_histories[session_id].append({"role": "user", "content": payload.query})
            _session_histories[session_id].append({"role": "assistant", "content": gen})
            _persist_query_to_db(
                session_id=session_id,
                tenant_id=payload.tenant_id,
                user_id=payload.user_id,
                query=payload.query,
                generation=gen,
                citations=final_state.get("citations", []),
                retrieved_chunks=final_state.get("documents", []),
                hallucination_status=final_state.get("hallucination_status", "grounded"),
                loop_count=final_state.get("loop_count", 0),
                rewritten_query=final_state.get("rewritten_query"),
                route=final_state.get("route", "vector_store"),
            )

        return QueryResponse(
            query=payload.query,
            generation=gen,
            citations=final_state.get("citations", []),
            hallucination_status=final_state.get("hallucination_status", "grounded"),
            fallback_reason=final_state.get("fallback_reason"),
            reasoning_trace=final_state.get("reasoning_trace", []),
            session_id=session_id,
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
    session_id = payload.session_id or "default_session"

    async def sse_event_stream() -> AsyncGenerator[Dict[str, Any], None]:
        # 1. Initial Start Event
        yield {
            "event": "status",
            "data": json.dumps({
                "phase": "initialized",
                "query": payload.query,
                "tenant_id": payload.tenant_id,
                "session_id": session_id,
            }),
        }
        await asyncio.sleep(0.01)

        last_generation = ""
        last_citations = []

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
                        last_generation = node_output["generation"]
                        last_citations = [
                            c.model_dump() if hasattr(c, "model_dump") else dict(c)
                            for c in node_output.get("citations", [])
                        ]
                        # Stream words as tokens for smooth UI typing animation
                        words = last_generation.split(" ")
                        for idx, word in enumerate(words):
                            token_str = word + (" " if idx < len(words) - 1 else "")
                            yield {
                                "event": "token",
                                "data": json.dumps({"token": token_str}),
                            }
                            await asyncio.sleep(0.01)

                        yield {
                            "event": "answer",
                            "data": json.dumps({
                                "generation": node_output["generation"],
                                "citations": last_citations,
                            }),
                        }
                        await asyncio.sleep(0.01)

                    # Stream refusal when fallback executes
                    if node_name == "fallback" and "generation" in node_output:
                        last_generation = node_output["generation"]
                        words = last_generation.split(" ")
                        for idx, word in enumerate(words):
                            token_str = word + (" " if idx < len(words) - 1 else "")
                            yield {
                                "event": "token",
                                "data": json.dumps({"token": token_str}),
                            }
                            await asyncio.sleep(0.01)

                        yield {
                            "event": "fallback",
                            "data": json.dumps({
                                "generation": node_output["generation"],
                                "reason": node_output.get("fallback_reason", "loop_ceiling_exhausted"),
                            }),
                        }
                        await asyncio.sleep(0.01)

            # Failsafe: If no generation was captured, produce honest fallback refusal
            if not last_generation:
                last_generation = (
                    "Unable to provide a verified answer with zero-hallucination certainty.\n\n"
                    "The available enterprise documents do not contain verified clauses matching this request. "
                    "In adherence to Axiom's Epistemic Humility principle, the SCORE engine refuses to extrapolate without explicit context."
                )
                yield {
                    "event": "answer",
                    "data": json.dumps({
                        "generation": last_generation,
                        "citations": [],
                    }),
                }
                await asyncio.sleep(0.01)

            # Persist turn in conversation history and SQLite DB
            if last_generation:
                _session_histories[session_id].append({"role": "user", "content": payload.query})
                _session_histories[session_id].append({"role": "assistant", "content": last_generation})
                _persist_query_to_db(
                    session_id=session_id,
                    tenant_id=payload.tenant_id,
                    user_id=payload.user_id,
                    query=payload.query,
                    generation=last_generation,
                    citations=last_citations,
                )

            # 3. Stream Completion Event
            yield {
                "event": "done",
                "data": json.dumps({
                    "status": "completed",
                    "session_id": session_id,
                    "final_generation": last_generation,
                }),
            }
            await asyncio.sleep(0.01)
        except Exception as exc:
            yield {
                "event": "error",
                "data": json.dumps({"error": str(exc)}),
            }

    return EventSourceResponse(sse_event_stream())
