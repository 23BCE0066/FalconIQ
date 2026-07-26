"""
Pydantic Domain Model: ToolResult

The standardized response envelope that every tool in FalconIQ must return.
The Supervisor Agent reads only this interface — it never reaches into tool internals.

Design:
- `success` drives the Supervisor's fallback logic.
- `confidence` feeds into the Risk Engine's weighted scoring.
- `explanation` surfaces directly to the Explainer Tool and frontend timeline.
- `metadata` carries tool-specific telemetry (row counts, model params, etc.)
"""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ToolResult(BaseModel):
    """
    Standardized response returned by every FalconIQ tool.

    Immutable once created. The Supervisor writes this into the
    ExecutionContext's `tool_outputs` dictionary keyed by tool name.
    """

    success: bool = Field(description="Whether this tool completed without a hard failure")
    status: str = Field(description="Short status string: 'completed', 'failed', 'skipped', 'partial'")
    tool_name: str = Field(description="Canonical name of the tool that produced this result")
    request_id: Optional[str] = Field(default=None, description="Request correlation ID")
    execution_time_ms: float = Field(ge=0.0, description="Wall-clock execution time in milliseconds")
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Tool confidence in its output, 0.0–1.0 (used by Risk Engine)"
    )
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Primary output payload — tool-specific structured data"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Non-fatal warnings raised during execution"
    )
    errors: List[str] = Field(
        default_factory=list,
        description="Error messages if the tool encountered failures"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Tool telemetry: row_count, model_version, thresholds used, etc."
    )
    explanation: str = Field(
        default="",
        description="Human-readable explanation of what this tool step found or did"
    )

    @classmethod
    def failure(
        cls,
        tool_name: str,
        error: str,
        execution_time_ms: float = 0.0,
    ) -> "ToolResult":
        """Factory method for producing a standard failure result."""
        return cls(
            success=False,
            status="failed",
            tool_name=tool_name,
            execution_time_ms=execution_time_ms,
            confidence=0.0,
            errors=[error],
            explanation=f"Tool '{tool_name}' failed: {error}",
        )

    @classmethod
    def skipped(cls, tool_name: str, reason: str) -> "ToolResult":
        """Factory method for producing a skipped-step result."""
        return cls(
            success=True,
            status="skipped",
            tool_name=tool_name,
            execution_time_ms=0.0,
            confidence=1.0,
            explanation=f"Tool '{tool_name}' was skipped: {reason}",
        )
