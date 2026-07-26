"""
Workflow Builder

Converts a PlannerAgent ExecutionPlan into a validated, dependency-ordered
list of tool names that the Supervisor will execute.

Why a separate WorkflowBuilder?
- The Planner's job is intent detection and filter extraction.
- The WorkflowBuilder's job is translating intent into a safe execution sequence.
- Separation keeps prompt engineering decoupled from execution logic.
- Allows deterministic fallback workflows when Planner confidence is low.

Dependency Rules (enforced, never rely solely on Planner ordering):
1. `dataset` must always be first.
2. `feature` must come before `rule_engine`, `ml_engine`, `risk_calculator`.
3. `risk_calculator` must come before `explainer`.
4. `explainer` must come before `report_writer`.
5. No duplicate tools are allowed.
"""
from typing import Dict, List

from app.constants import AMLPattern, PlannerIntent, ToolName
from app.core.exceptions import ValidationException
from app.logging.logger import get_logger
from app.schemas.execution_plan import ExecutionPlan

logger = get_logger(__name__)

# Canonical tool ordering — the authoritative sequence for known intent types.
# The Supervisor always executes in this order even if the Planner suggests otherwise.
CANONICAL_WORKFLOWS: Dict[PlannerIntent, List[ToolName]] = {
    PlannerIntent.STRUCTURING_DETECTION: [
        ToolName.DATASET,
        ToolName.FEATURE,
        ToolName.RULE_ENGINE,
        ToolName.RISK_CALCULATOR,
        ToolName.EXPLAINER,
    ],
    PlannerIntent.CUSTOMER_LOOKUP: [
        ToolName.DATASET,
        ToolName.FEATURE,
        ToolName.RISK_CALCULATOR,
        ToolName.EXPLAINER,
    ],
    PlannerIntent.HIGH_RISK_CUSTOMERS: [
        ToolName.DATASET,
        ToolName.FEATURE,
        ToolName.RULE_ENGINE,
        ToolName.ML_ENGINE,
        ToolName.RISK_CALCULATOR,
        ToolName.EXPLAINER,
    ],
    PlannerIntent.NETWORK_ANALYSIS: [
        ToolName.DATASET,
        ToolName.NETWORK_ANALYZER,
        ToolName.RISK_CALCULATOR,
        ToolName.EXPLAINER,
    ],
    PlannerIntent.EDA_REQUEST: [
        ToolName.DATASET,
        ToolName.EDA,
        ToolName.EXPLAINER,
    ],
    PlannerIntent.REPORT_GENERATION: [
        ToolName.DATASET,
        ToolName.FEATURE,
        ToolName.RULE_ENGINE,
        ToolName.RISK_CALCULATOR,
        ToolName.EXPLAINER,
        ToolName.REPORT_WRITER,
    ],
    PlannerIntent.GENERAL_INVESTIGATION: [
        ToolName.DATASET,
        ToolName.FEATURE,
        ToolName.RULE_ENGINE,
        ToolName.RISK_CALCULATOR,
        ToolName.EXPLAINER,
    ],
}

# Dependency map: a tool can only appear AFTER all its dependencies are present.
# Key = tool that has deps. Value = set of tools that must precede it.
TOOL_DEPENDENCIES: Dict[ToolName, List[ToolName]] = {
    ToolName.FEATURE: [ToolName.DATASET],
    ToolName.RULE_ENGINE: [ToolName.DATASET, ToolName.FEATURE],
    ToolName.ML_ENGINE: [ToolName.DATASET, ToolName.FEATURE],
    ToolName.RISK_CALCULATOR: [ToolName.DATASET, ToolName.FEATURE],
    ToolName.EXPLAINER: [ToolName.RISK_CALCULATOR],
    ToolName.REPORT_WRITER: [ToolName.EXPLAINER],
    ToolName.NETWORK_ANALYZER: [ToolName.DATASET],
    ToolName.EDA: [ToolName.DATASET],
}

# Minimum confidence below which we fall back to the canonical workflow
_CONFIDENCE_FALLBACK_THRESHOLD = 0.60


class WorkflowBuilder:
    """
    Converts a Planner ExecutionPlan into a dependency-validated tool sequence.

    The build() method:
    1. Checks Planner confidence — uses canonical workflow if too low.
    2. Starts from the Planner's tool list.
    3. Inserts missing mandatory dependencies.
    4. Enforces the canonical dependency ordering.
    5. Deduplicates while preserving order.
    6. Validates the final sequence.
    """

    def build(self, plan: ExecutionPlan) -> List[ToolName]:
        """
        Builds the final ordered tool execution sequence from an ExecutionPlan.

        Returns:
            Ordered list of ToolName values ready for Supervisor execution.

        Raises:
            ValidationException: If the resulting sequence violates dependency rules.
        """
        intent = plan.intent
        planner_tools = list(plan.tools)
        confidence = plan.confidence

        # Low-confidence fallback: use canonical workflow for the detected intent
        if confidence < _CONFIDENCE_FALLBACK_THRESHOLD:
            canonical = CANONICAL_WORKFLOWS.get(intent, CANONICAL_WORKFLOWS[PlannerIntent.GENERAL_INVESTIGATION])
            logger.warning(
                "workflow_builder_low_confidence_fallback",
                intent=intent,
                confidence=confidence,
                fallback_tools=[t.value for t in canonical],
            )
            return canonical

        # Start with the Planner's tool list and enforce mandatory dependencies
        resolved = self._inject_dependencies(planner_tools)

        # Sort by canonical ordering for this intent
        resolved = self._sort_by_canonical_order(resolved, intent)

        # Final deduplication (preserve order)
        resolved = self._deduplicate(resolved)

        # Validate dependency ordering of the final sequence
        self._validate_dependencies(resolved)

        logger.info(
            "workflow_built",
            intent=intent,
            tools=[t.value for t in resolved],
            tool_count=len(resolved),
        )
        return resolved

    def _inject_dependencies(self, tools: List[ToolName]) -> List[ToolName]:
        """
        Adds missing dependency tools to the list.

        Example: if `rule_engine` is present but `feature` is missing,
        `feature` is injected before `rule_engine`.
        """
        tool_set = set(tools)
        to_inject: List[ToolName] = []

        for tool in tools:
            deps = TOOL_DEPENDENCIES.get(tool, [])
            for dep in deps:
                if dep not in tool_set:
                    logger.info(
                        "workflow_dependency_injected",
                        tool=tool.value,
                        dependency=dep.value,
                    )
                    to_inject.append(dep)
                    tool_set.add(dep)

        # Prepend injected dependencies (they will be sorted properly next)
        return to_inject + tools

    def _sort_by_canonical_order(
        self, tools: List[ToolName], intent: PlannerIntent
    ) -> List[ToolName]:
        """
        Sorts the tool list according to the canonical execution order for
        the given intent. Tools not in the canonical list are appended at end.
        """
        canonical = CANONICAL_WORKFLOWS.get(intent, CANONICAL_WORKFLOWS[PlannerIntent.GENERAL_INVESTIGATION])
        canonical_order = {tool: idx for idx, tool in enumerate(canonical)}

        # Tools with known canonical position sort by index; unknown tools sort last
        return sorted(tools, key=lambda t: canonical_order.get(t, 999))

    def _deduplicate(self, tools: List[ToolName]) -> List[ToolName]:
        """Removes duplicate tool entries while preserving order."""
        seen: set = set()
        result: List[ToolName] = []
        for tool in tools:
            if tool not in seen:
                seen.add(tool)
                result.append(tool)
        return result

    def _validate_dependencies(self, tools: List[ToolName]) -> None:
        """
        Validates that all dependency constraints are satisfied in the
        final ordered tool sequence.

        Raises:
            ValidationException: If a tool appears before its required dependency.
        """
        seen: set = set()
        for tool in tools:
            deps = TOOL_DEPENDENCIES.get(tool, [])
            unsatisfied = [d.value for d in deps if d not in seen]
            if unsatisfied:
                raise ValidationException(
                    f"Tool '{tool.value}' appears before its required "
                    f"dependencies: {unsatisfied}. "
                    f"Current sequence: {[t.value for t in tools]}"
                )
            seen.add(tool)
