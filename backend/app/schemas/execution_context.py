"""
Pydantic Domain Model: ExecutionContext

The shared runtime scratchpad that travels through the entire Supervisor loop.
Every tool receives the same context instance and writes its outputs into it.

Design Principles:
- Single context per request (one-to-one with AgentSession).
- Tools never reload data if it is already cached in `dataframes`.
- All state mutations happen via helper methods — never direct dict access.
- The context is serializable to JSON for logging and persistence.
"""
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr

from app.constants import SessionStatus
from app.schemas.execution_plan import ExecutionPlan
from app.schemas.tool_result import ToolResult
from app.utils.id_generator import generate_session_id
from app.utils.time import utcnow


class ExecutionContext(BaseModel):
    """
    Shared execution state for a single agent investigation session.

    Lifecycle:
    1. Created by the Supervisor at the start of each request.
    2. Passed to every tool in the execution plan.
    3. Each tool reads inputs from context and writes ToolResult back.
    4. After all tools complete, the Supervisor reads final state for response.
    """

    # Session identity
    session_id: str = Field(default_factory=generate_session_id)
    query: str = Field(description="Original user natural language query")
    request_id: Optional[str] = Field(default=None, description="HTTP request ID from middleware for tracing")

    # Execution plan (set after Planner runs)
    execution_plan: Optional[ExecutionPlan] = Field(default=None)

    # Execution state tracking
    current_step: int = Field(default=0, description="Zero-indexed current tool step")
    completed_tools: List[str] = Field(default_factory=list)
    failed_tools: List[str] = Field(default_factory=list)
    skipped_tools: List[str] = Field(default_factory=list)

    # Tool outputs — keyed by tool name
    tool_outputs: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Serialized ToolResult.data from each completed tool"
    )

    # Shared typed variables (string keys to domain values)
    variables: Dict[str, Any] = Field(
        default_factory=dict,
        description="Named variables accessible across tools (e.g. risk_score, customer_id)"
    )

    # Accumulated warnings and errors across all tools
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)

    # Execution Timeline
    execution_timeline: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Chronological log of executed tools and their timings"
    )

    # Execution metadata
    status: SessionStatus = Field(default=SessionStatus.RUNNING)
    started_at: datetime = Field(default_factory=utcnow)
    completed_at: Optional[datetime] = Field(default=None)

    # Performance Metrics
    performance_metrics: Dict[str, float] = Field(
        default_factory=lambda: {
            "database_time_ms": 0.0,
            "tool_time_ms": 0.0,
            "planner_time_ms": 0.0,
            "llm_time_ms": 0.0,
            "workflow_time_ms": 0.0,
            "total_runtime_ms": 0.0,
        },
        description="Detailed execution timing breakdown"
    )

    # DataFrames are not Pydantic-serializable — stored as private attributes
    _dataframes: Dict[str, pd.DataFrame] = PrivateAttr(default_factory=dict)
    _features_cache: Dict[str, Any] = PrivateAttr(default_factory=dict)
    _rules_cache: Dict[str, Any] = PrivateAttr(default_factory=dict)
    _start_time: float = PrivateAttr(default_factory=time.perf_counter)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    # ── DataFrame Cache ────────────────────────────────────────────────────────

    def get_df(self, key: str) -> Optional[pd.DataFrame]:
        """Retrieves a cached DataFrame by key. Returns None if not found."""
        return self._dataframes.get(key)

    def set_df(self, key: str, df: pd.DataFrame) -> None:
        """Caches a DataFrame under the given key for reuse by downstream tools."""
        self._dataframes[key] = df

    def has_df(self, key: str) -> bool:
        """Returns True if a DataFrame with the given key exists in cache."""
        return key in self._dataframes

    def list_dfs(self) -> List[str]:
        """Returns the list of cached DataFrame keys."""
        return list(self._dataframes.keys())

    # ── Variable Store ─────────────────────────────────────────────────────────

    def get_var(self, key: str, default: Any = None) -> Any:
        """Retrieves a named variable from the shared variable store."""
        return self.variables.get(key, default)

    def set_var(self, key: str, value: Any) -> None:
        """Sets a named variable in the shared variable store."""
        self.variables[key] = value

    # ── Specialized Caches ─────────────────────────────────────────────────────

    def get_cached_features(self, key: str) -> Optional[Any]:
        return self._features_cache.get(key)

    def set_cached_features(self, key: str, features: Any) -> None:
        self._features_cache[key] = features

    def get_cached_rules(self, key: str) -> Optional[Any]:
        return self._rules_cache.get(key)

    def set_cached_rules(self, key: str, rules: Any) -> None:
        self._rules_cache[key] = rules

    # ── Tool Output Store ──────────────────────────────────────────────────────

    def record_tool_result(self, result: ToolResult) -> None:
        """
        Records a completed ToolResult into the context.
        Updates completed_tools, failed_tools, and stores the serialized data.
        """
        if result.success:
            if result.status != "skipped":
                self.completed_tools.append(result.tool_name)
            else:
                self.skipped_tools.append(result.tool_name)
        else:
            self.failed_tools.append(result.tool_name)
            self.errors.extend(result.errors)

        self.warnings.extend(result.warnings)
        self.tool_outputs[result.tool_name] = result.data
        
        self.execution_timeline.append({
            "tool": result.tool_name,
            "duration_ms": result.execution_time_ms,
            "status": result.status
        })
        
        self.current_step += 1

    def get_tool_output(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Retrieves stored output data from a previously executed tool."""
        return self.tool_outputs.get(tool_name)

    # ── Lifecycle Helpers ──────────────────────────────────────────────────────

    def mark_completed(self) -> None:
        """Marks the session as successfully completed."""
        self.status = SessionStatus.COMPLETED
        self.completed_at = utcnow()

    def mark_failed(self, reason: str) -> None:
        """Marks the session as failed and records the failure reason."""
        self.status = SessionStatus.FAILED
        self.completed_at = utcnow()
        self.errors.append(reason)

    def total_elapsed_ms(self) -> float:
        """Returns total wall-clock time since context was created, in ms."""
        elapsed = round((time.perf_counter() - self._start_time) * 1000, 3)
        self.performance_metrics["total_runtime_ms"] = elapsed
        return elapsed

    def add_metric(self, key: str, elapsed_ms: float) -> None:
        """Adds time to a specific performance metric."""
        if key in self.performance_metrics:
            self.performance_metrics[key] += round(elapsed_ms, 3)

    def has_hard_failures(self) -> bool:
        """Returns True if any tool failed (not just raised warnings)."""
        return len(self.failed_tools) > 0

    def is_tool_completed(self, tool_name: str) -> bool:
        """Returns True if the named tool has already successfully completed."""
        return tool_name in self.completed_tools
