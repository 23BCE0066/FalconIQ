"""
Validator: ExecutionPlanValidator

Validates the structured output of the Planner Agent before the Supervisor
begins tool orchestration. This is the critical safety net between LLM output
and live execution — preventing malformed plans from causing runtime errors.
"""
from typing import List

from app.agents.registry import ToolRegistry
from app.core.exceptions import ValidationException
from app.schemas.execution_plan import ExecutionPlan


class ExecutionPlanValidator:
    """
    Validates ExecutionPlan objects before execution.

    Checks:
    1. Plan contains at least one tool.
    2. No duplicate tools in the plan.
    3. All tool names exist in the ToolRegistry.
    4. Confidence score is within valid bounds.
    """

    def __init__(self, registry: ToolRegistry) -> None:
        self._registry = registry

    def validate(self, plan: ExecutionPlan) -> None:
        """
        Validates the execution plan against the tool registry.
        Raises ValidationException with a descriptive message on first failure.
        """
        if not plan.tools:
            raise ValidationException(
                "ExecutionPlan contains no tools. Planner must select at least one tool."
            )

        # Duplicate check (also enforced at model level, but double-checked here)
        tool_names = [t.value for t in plan.tools]
        if len(tool_names) != len(set(tool_names)):
            duplicates = [n for n in tool_names if tool_names.count(n) > 1]
            raise ValidationException(
                f"ExecutionPlan contains duplicate tools: {list(set(duplicates))}"
            )

        # Registry existence check
        unregistered = [
            name for name in tool_names if not self._registry.exists(name)
        ]
        if unregistered:
            available = self._registry.list_tools()
            raise ValidationException(
                f"ExecutionPlan references unregistered tools: {unregistered}. "
                f"Available tools: {available}"
            )

        # Confidence check
        if not (0.0 <= plan.confidence <= 1.0):
            raise ValidationException(
                f"ExecutionPlan confidence '{plan.confidence}' is outside valid range [0.0, 1.0]."
            )
