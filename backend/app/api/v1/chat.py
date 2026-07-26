"""
Router: Chat (AI Investigation)

POST /api/v1/chat — Main entry point for all AI investigation requests.

Improved in Phase 5:
    - Full conversation history support
    - Request metadata propagation
    - Planner confidence in response
    - Execution timeline in response
    - Citations support (when Explainer provides them)
    - Streaming-ready design (SSE flag in request)
    - Standard ResponseEnvelope wrapping
"""
from typing import Annotated, Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from app.agents.supervisor.agent import SupervisorAgent
from app.api.common.response_envelope import RequestContext, get_request_context
from app.constants import SessionStatus
from app.core.dependencies import get_supervisor_agent
from app.logging.logger import get_logger
from app.schemas.chat import ChatRequest, ChatResponse
from sqlmodel import Session as DbSession, select
from app.database.engine import get_session
from app.database.models.session import AgentSession
from app.database.models.execution_log import AgentExecutionLog
from app.api.common.response_mapper import ResponseMapper

router = APIRouter()
logger = get_logger(__name__)


# ── Enhanced Request ───────────────────────────────────────────────────────────

class ConversationTurn(BaseModel):
    """A single turn in a multi-turn conversation history."""
    role: str = Field(description="'user' or 'assistant'")
    content: str = Field(description="Turn content")


class InvestigationChatRequest(BaseModel):
    """
    Enhanced request body for POST /api/v1/chat.

    Supports multi-turn conversation, streaming hints, and metadata.
    """
    query: str = Field(
        min_length=5,
        max_length=2000,
        description="Natural language investigation query from the compliance officer",
        examples=["Detect structuring patterns for customer cust_abc123 in the last 90 days"],
    )
    request_id: Optional[str] = Field(
        default=None,
        description="Optional client-provided trace ID for correlation",
    )
    conversation_history: List[ConversationTurn] = Field(
        default_factory=list,
        description="Previous conversation turns for multi-turn investigations",
    )
    stream: bool = Field(
        default=False,
        description="Reserved for future streaming support — currently ignored",
    )
    context_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Optional caller metadata (e.g. analyst ID, case number)",
    )


# ── Endpoint ───────────────────────────────────────────────────────────────────

@router.post(
    "/chat",
    summary="Submit an AML investigation query",
    description=(
        "The primary AI investigation endpoint. Accepts a natural language query from a "
        "compliance officer and returns a full investigation response.\n\n"
        "**Workflow:**\n"
        "1. Planner Agent analyses the query and produces an execution plan.\n"
        "2. Supervisor Agent orchestrates tool execution.\n"
        "3. Explainer produces a human-readable summary with citations.\n"
        "4. All results are returned in a standard ResponseEnvelope.\n\n"
        "**Response includes:**\n"
        "- Planner confidence score\n"
        "- Tool execution timeline\n"
        "- Risk scores and evidence\n"
        "- Explainer summary with citations (when available)\n"
        "- Full execution metadata\n"
    ),
    response_description="Complete AI investigation response.",
    tags=["Chat"],
    responses={
        200: {
            "description": "Investigation completed successfully.",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": {
                            "session_id": "sess_abc123",
                            "query": "Detect structuring for customer cust_xyz",
                            "status": "COMPLETED",
                            "intent": "STRUCTURING_DETECTION",
                            "summary": "Customer shows structuring behavior across 12 transactions.",
                            "planner_confidence": 0.94,
                            "execution_timeline": [],
                            "data": {},
                        },
                        "metadata": {
                            "request_id": "req_abc",
                            "execution_time_ms": 3200.4,
                            "timestamp": "2026-01-01T00:00:00+00:00",
                            "version": "v1",
                        },
                    }
                }
            },
        },
        400: {"description": "Invalid query or planning failure."},
        422: {"description": "Query too short, too long, or malformed."},
        503: {"description": "AI service unavailable."},
    },
)
async def chat(
    body: InvestigationChatRequest,
    request: Request,
    ctx: Annotated[RequestContext, Depends(get_request_context)],
    supervisor: Annotated[SupervisorAgent, Depends(get_supervisor_agent)],
) -> dict:
    """
    Submits a natural language AML investigation query.

    The Planner dynamically determines which tools to execute.
    Results include the full execution timeline, risk scores, and an
    Explainer-generated summary with supporting evidence.
    """
    # Prefer header request_id, fall back to body-provided, then context
    request_id: str = (
        request.headers.get("X-Request-ID")
        or body.request_id
        or ctx.request_id
    )

    logger.info(
        "chat_investigation_started",
        request_id=request_id,
        query_length=len(body.query),
        has_history=len(body.conversation_history) > 0,
        context_metadata=body.context_metadata,
    )

    # Delegate to SupervisorAgent (unchanged from Phase 4)
    result: ChatResponse = await supervisor.process(
        query=body.query,
        request_id=request_id,
    )

    # Build enriched response payload (no internal types exposed)
    response_data = {
        "session_id": result.session_id,
        "query": result.query,
        "request_id": request_id,
        "status": result.status.value if hasattr(result.status, "value") else str(result.status),
        "intent": result.intent,
        "execution_plan": result.execution_plan,
        "completed_tools": result.completed_tools,
        "failed_tools": result.failed_tools,
        "skipped_tools": result.skipped_tools,
        "tool_count": result.tool_count,
        "planner_confidence": result.planner_confidence,
        "risk_confidence": result.risk_confidence,
        "summary": result.summary,
        "data": result.data,
        "execution_timeline": [
            {
                "tool_name": step.tool_name,
                "step_order": step.step_order,
                "success": step.success,
                "status": step.status,
                "execution_time_ms": step.execution_time_ms,
                "confidence": step.confidence,
                "explanation": step.explanation,
            }
            for step in result.execution_timeline
        ],
        "total_execution_time_ms": result.total_execution_time_ms,
        "warnings": result.warnings,
        "errors": result.errors,
        "citations": result.data.get("citations", []),
        "conversation_history": [t.model_dump() for t in body.conversation_history],
        "metadata": result.metadata,
    }

    logger.info(
        "chat_investigation_completed",
        request_id=request_id,
        session_id=result.session_id,
        status=str(result.status),
        tool_count=result.tool_count,
        total_ms=result.total_execution_time_ms,
    )

    return ctx.ok(response_data)

@router.get(
    "/chat/sessions/{session_id}",
    summary="Get full chat session history",
    tags=["Chat"],
)
async def get_chat_session(
    ctx: Annotated[RequestContext, Depends(get_request_context)],
    session_id: str,
    db: Annotated[DbSession, Depends(get_session)],
) -> dict:
    session_orm = db.get(AgentSession, session_id)
    if not session_orm:
        return ctx.ok({"error": "Session not found"})
        
    logs_stmt = select(AgentExecutionLog).where(AgentExecutionLog.session_id == session_id).order_by(AgentExecutionLog.step_order)
    logs = db.exec(logs_stmt).all()
    
    # Manually map session and logs to ChatResponse format
    response_data = {
        "session_id": session_orm.session_id,
        "query": session_orm.query,
        "status": session_orm.status.value if hasattr(session_orm.status, "value") else str(session_orm.status),
        "intent": session_orm.intent,
        "execution_plan": session_orm.execution_plan,
        "total_execution_time_ms": session_orm.total_execution_time_ms,
        "execution_timeline": [
            {
                "tool_name": step.tool_name,
                "step_order": step.step_order,
                "success": step.success,
                "execution_time_ms": step.execution_time_ms,
                "confidence": step.confidence,
                "explanation": step.explanation,
                "output_payload": step.output_payload,
            }
            for step in logs
        ]
    }
    return ctx.ok(response_data)
