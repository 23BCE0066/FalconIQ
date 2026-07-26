"""
SQLModel Domain Model: AgentSession

Records the lifecycle of a single Planner + Supervisor agent execution.
Every chat request creates exactly one AgentSession, enabling full audit trails.
"""
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel

from app.constants import SessionStatus
from app.utils.id_generator import generate_session_id
from app.utils.time import utcnow


class AgentSession(SQLModel, table=True):
    """
    Persisted agent session entity.

    Captures the user query, the execution plan produced by the Planner,
    runtime status, and any errors encountered during tool orchestration.
    """

    __tablename__ = "agent_sessions"

    session_id: str = Field(
        default_factory=generate_session_id,
        primary_key=True,
        description="Unique session identifier (e.g. sess_abc123)"
    )
    query: str = Field(description="Original natural language query from the user")
    execution_plan: Optional[str] = Field(
        default=None, description="JSON-serialized ordered list of tool names"
    )
    intent: Optional[str] = Field(default=None, description="Planner-detected intent")
    status: SessionStatus = Field(default=SessionStatus.RUNNING, description="Session lifecycle status")
    current_tool: Optional[str] = Field(default=None, description="Currently executing tool name")
    error_log: Optional[str] = Field(default=None, description="Accumulated error messages if session failed")
    total_execution_time_ms: Optional[float] = Field(default=None, description="Total wall-clock time in ms")
    created_at: datetime = Field(default_factory=utcnow)
    completed_at: Optional[datetime] = Field(default=None)
