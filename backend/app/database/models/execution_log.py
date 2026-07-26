"""
SQLModel Domain Model: AgentExecutionLog

Immutable log of every tool invocation within a session.
Each row represents one tool execution step: its inputs, outputs, timing, and
the human-readable explanation produced by that tool.

These logs power the execution trace timeline in the frontend.
"""
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel

from app.utils.id_generator import generate_log_id
from app.utils.time import utcnow


class AgentExecutionLog(SQLModel, table=True):
    """
    Immutable tool execution log — one row per tool invocation.

    Indexed on session_id for fast retrieval of all steps for a given session.
    """

    __tablename__ = "agent_execution_logs"

    log_id: str = Field(
        default_factory=generate_log_id,
        primary_key=True,
        description="Unique log entry identifier"
    )
    session_id: str = Field(
        index=True,
        description="Foreign key to agent_sessions.session_id"
    )
    tool_name: str = Field(description="Name of the tool that was executed")
    step_order: int = Field(ge=0, description="Zero-indexed step position in the execution plan")
    success: bool = Field(description="Whether the tool completed without error")
    input_payload: Optional[str] = Field(
        default=None, description="JSON-serialized snapshot of relevant context keys used as input"
    )
    output_payload: Optional[str] = Field(
        default=None, description="JSON-serialized ToolResult data field"
    )
    start_time: Optional[datetime] = Field(default=None, description="Tool execution start timestamp")
    end_time: Optional[datetime] = Field(default=None, description="Tool execution end timestamp")
    execution_time_ms: float = Field(ge=0, description="Wall-clock execution time for this tool in ms")
    duration_ms: Optional[float] = Field(default=None, ge=0, description="Alias for execution_time_ms to satisfy audit trail")
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Tool confidence score (0–1)")
    explanation: Optional[str] = Field(default=None, description="Human-readable explanation from the tool")
    warnings: Optional[str] = Field(default=None, description="JSON-serialized warnings from tool execution")
    summary: Optional[str] = Field(default=None, description="Short summary of tool results")
    error_message: Optional[str] = Field(default=None, description="Error detail if the tool failed")
    created_at: datetime = Field(default_factory=utcnow)
