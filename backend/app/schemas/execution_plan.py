"""
Pydantic Domain Model: ExecutionPlan

Structured output produced by the Planner Agent after parsing a natural language query.
The Planner emits one ExecutionPlan per request; the Workflow Builder consumes it
to resolve the ordered tool DAG.

Critical: All field types use strict Pydantic validation so that a malformed LLM
response triggers a ValidationException rather than propagating silently.
"""
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from app.constants import AMLPattern, PlannerIntent, ToolName


class FilterParams(BaseModel):
    """Time and entity filters extracted from the user query."""

    days: Optional[int] = Field(default=None, ge=1, le=365, description="Rolling time window in days")
    customer_id: Optional[str] = Field(default=None, description="Specific customer entity to investigate")
    min_amount: Optional[float] = Field(default=None, ge=0, description="Minimum transaction amount filter")
    max_amount: Optional[float] = Field(default=None, ge=0, description="Maximum transaction amount filter")
    country: Optional[str] = Field(default=None, description="Country filter (ISO 3166-1 alpha-3)")


class ExecutionPlan(BaseModel):
    """
    Structured output of the Planner Agent.

    The `tools` field is an ordered list of ToolName values representing
    the minimal execution DAG required to answer the user's query.
    The Supervisor executes them in this exact order.
    """

    intent: PlannerIntent = Field(description="Detected intent of the user query")
    aml_pattern: Optional[AMLPattern] = Field(
        default=None, description="AML pattern the query is targeting, if applicable"
    )
    entities: List[str] = Field(
        default_factory=list,
        description="Named entities extracted (e.g. customer IDs, transaction IDs)"
    )
    filters: FilterParams = Field(
        default_factory=FilterParams,
        description="Extracted filter parameters from the query"
    )
    tools: List[ToolName] = Field(
        min_length=1,
        description="Ordered list of tools to execute — minimum one tool required"
    )
    confidence: float = Field(
        default=1.0, ge=0.0, le=1.0,
        description="Planner confidence in the correctness of this execution plan"
    )
    reasoning: str = Field(
        default="",
        description="Planner's step-by-step reasoning for the tool selection (for transparency)"
    )

    @field_validator("tools")
    @classmethod
    def tools_must_be_unique_and_ordered(cls, tools: List[ToolName]) -> List[ToolName]:
        """Ensures no tool appears twice in the plan — prevents infinite loops."""
        if len(tools) != len(set(tools)):
            raise ValueError("Execution plan contains duplicate tool entries.")
        return tools
