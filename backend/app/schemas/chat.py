"""
API Schemas: Chat endpoint request and response models.
"""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.constants import SessionStatus
from app.schemas.tool_result import ToolResult


class ChatRequest(BaseModel):
    """Request body for POST /api/v1/chat."""
    query: str = Field(
        min_length=5,
        max_length=2000,
        description="Natural language investigation query from the compliance officer"
    )
    request_id: Optional[str] = Field(default=None, description="Optional client-provided trace ID")


class ToolExecutionSummary(BaseModel):
    """Compact summary of a single tool execution step — used in the response timeline."""
    tool_name: str
    step_order: int
    success: bool
    status: str
    execution_time_ms: float
    confidence: float
    explanation: str


class ChatResponse(BaseModel):
    """Response body for POST /api/v1/chat."""
    request_id: Optional[str] = Field(default=None, description="Request correlation ID")
    session_id: str
    query: str
    status: SessionStatus
    intent: Optional[str] = None
    execution_plan: List[str] = Field(description="Ordered list of tools that were resolved")
    completed_tools: List[str]
    failed_tools: List[str]
    skipped_tools: List[str]
    tool_count: int = Field(default=0, description="Total number of tools executed")
    planner_confidence: Optional[float] = Field(default=None, description="Confidence score from PlannerAgent")
    risk_confidence: Optional[float] = Field(default=None, description="Confidence score from Risk Engine")
    summary: str = Field(description="High-level Explainer summary for display in the UI")
    data: Dict[str, Any] = Field(description="Aggregated data outputs from all tools")
    execution_timeline: List[ToolExecutionSummary] = Field(description="Per-tool execution trace")
    total_execution_time_ms: float
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Execution performance metrics")
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
