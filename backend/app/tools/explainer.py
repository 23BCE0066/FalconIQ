"""
Tool: ExplainerTool (Production Implementation)

Generates human-readable AML investigation explanations using Gemini.
Extracts relevant context from ExecutionContext and passes a structured
JSON payload to the ExplainerService.
"""
from typing import Any, Dict

from app.constants import ToolName
from app.interfaces.tools import BaseTool
from app.schemas.execution_context import ExecutionContext
from app.schemas.tool_result import ToolResult
from app.services.explainer import ExplainerService


class ExplainerTool(BaseTool):
    """Generates human-readable compliance explanations of investigation findings."""

    def __init__(self, explainer_service: ExplainerService) -> None:
        self._service = explainer_service

    @property
    def name(self) -> str:
        return ToolName.EXPLAINER

    @property
    def description(self) -> str:
        return (
            "Generates a human-readable investigation explanation using Gemini. "
            "Explains why a customer was flagged, which rules triggered, "
            "ML confidence, and recommended compliance actions. "
            "Requires risk_calculator output."
        )

    async def _run(self, context: ExecutionContext) -> ToolResult:
        # Build the structured payload for Gemini
        payload: Dict[str, Any] = {
            "customer_id": context.get_var("filter_customer_id"),
            "risk_score": context.get_var("risk_score", 0.0),
            "risk_level": context.get_var("risk_level", "UNKNOWN"),
        }

        # Add rule engine results if available
        rule_results = context.get_var("rule_results", {})
        if rule_results:
            payload["triggered_rules"] = rule_results.get("triggered_rules", [])
            payload["rules_evaluated"] = rule_results.get("rules_evaluated", 0)

        # Add ML results if available
        ml_score = context.get_var("ml_score")
        if ml_score is not None:
            payload["anomaly_score"] = ml_score

        # Add global context if we did a global sweep
        if not payload["customer_id"]:
            payload["mode"] = "global_sweep"
            # In global mode, summarize top offenders
            ml_dict = context.get_var("ml_scores_dict")
            if ml_dict and isinstance(ml_dict, dict):
                top_ml = sorted(ml_dict.items(), key=lambda x: -x[1])[:5]
                payload["top_anomalous_customers"] = top_ml

        # Add dataset context
        payload["dataset_summary"] = {
            "records_analyzed": context.get_var("record_count", 0),
            "days_lookback": context.get_var("filter_days"),
        }

        import time
        t_llm_start = time.perf_counter()
        response = self._service.generate_explanation(payload)
        context.add_metric("llm_time_ms", (time.perf_counter() - t_llm_start) * 1000)

        # Store results back in context
        context.set_var("explanation", response.executive_summary)
        context.set_var("recommendation", response.compliance_recommendation)
        context.set_var("detailed_explanation", response.detailed_explanation)

        return ToolResult(
            success=True,
            status="completed",
            tool_name=self.name,
            execution_time_ms=0.0,
            confidence=0.95,
            data=response.model_dump(),
            explanation=response.executive_summary,
            metadata={"model": "gemini-2.5-flash"},
        )
