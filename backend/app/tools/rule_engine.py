"""
Tool: RuleEngineTool (Production Implementation)

Runs all enabled AML rules against the feature vector and raw transactions.
Aggregates results and writes scores into ExecutionContext.
"""
from typing import Any, Dict, List, Optional

import pandas as pd

from app.constants import ToolName
from app.interfaces.tools import BaseTool
from app.rule_engine.base import RuleResult
from app.rule_engine.rules import (
    CrossBorderRule,
    DormantAccountRule,
    LayeringRule,
    RapidCashOutRule,
    StructuringRule,
    VelocityRule,
)
from app.schemas.execution_context import ExecutionContext
from app.schemas.tool_result import ToolResult
from app.services.dataset import DatasetService

# Ordered list of all registered rules
_ALL_RULES = [
    StructuringRule(),
    VelocityRule(),
    RapidCashOutRule(),
    LayeringRule(),
    CrossBorderRule(),
    DormantAccountRule(),
]


class RuleEngineTool(BaseTool):
    """
    Evaluates all enabled AML rules against computed features.
    Each rule is independent and produces its own RuleResult.
    Aggregated rule scores feed into the RiskCalculatorTool.
    """

    @property
    def name(self) -> str:
        return ToolName.RULE_ENGINE

    @property
    def description(self) -> str:
        return (
            "Applies 6 deterministic AML rules: structuring, velocity, rapid cash-out, "
            "layering, cross-border, and dormant account. Requires feature tool output."
        )

    async def _run(self, context: ExecutionContext) -> ToolResult:
        features = context.get_var("features")
        if not features:
            return ToolResult.failure(
                self.name, "Feature vector not found. FeatureTool must run first."
            )

        cached_rules = context.get_cached_rules("rule_results")
        if cached_rules is not None:
            rule_score = cached_rules["total_rule_score"]
            triggered = cached_rules["triggered_rules"]
            return ToolResult(
                success=True,
                status="completed",
                tool_name=self.name,
                execution_time_ms=0.0,
                confidence=0.90,
                data={
                    "rules_evaluated": cached_rules["rules_evaluated"],
                    "rules_triggered": cached_rules["rules_triggered"],
                    "triggered_rules": triggered,
                    "total_rule_score": rule_score,
                    "rule_details": cached_rules["results"],
                },
                explanation=(
                    f"Evaluated {cached_rules['rules_evaluated']} AML rules (from cache). "
                    f"{cached_rules['rules_triggered']} triggered. Combined rule score: {rule_score:.1f}/100."
                ),
                metadata={"rule_count": len(_ALL_RULES), "cached": True},
            )

        df: Optional[pd.DataFrame] = context.get_df(DatasetService.DF_TRANSACTIONS)
        customer_id = context.get_var("filter_customer_id")

        # If global mode: features is a dict of {customer_id: feature_dict}
        # If single customer mode: features is the feature dict directly
        if isinstance(features, dict) and customer_id:
            # Single customer: features is the flat dict
            results = self._run_rules(features, df)
        elif isinstance(features, dict):
            # Global mode: aggregate across all customers, report worst offenders
            results = self._run_global_rules(features, df)
        else:
            return ToolResult.failure(self.name, "Unexpected feature format in context.")

        triggered = [r for r in results if r.triggered]
        total_score = min(100.0, sum(r.score for r in triggered))
        rule_score = total_score

        context.set_var("rule_results", {
            "results": [r.to_dict() for r in results],
            "triggered_rules": [r.rule_name for r in triggered],
            "total_rule_score": rule_score,
            "rules_evaluated": len(results),
            "rules_triggered": len(triggered),
        })
        context.set_cached_rules("rule_results", context.get_var("rule_results"))
        context.set_var("rule_score", rule_score)
        context.set_var("triggered_rules", [r.rule_name for r in triggered])

        triggered_names = [r.rule_name for r in triggered]
        explanation = (
            f"Evaluated {len(results)} AML rules. "
            f"{len(triggered)} triggered: {', '.join(triggered_names) or 'none'}. "
            f"Combined rule score: {rule_score:.1f}/100."
        )

        return ToolResult(
            success=True,
            status="completed",
            tool_name=self.name,
            execution_time_ms=0.0,
            confidence=0.90,
            data={
                "rules_evaluated": len(results),
                "rules_triggered": len(triggered),
                "triggered_rules": triggered_names,
                "total_rule_score": rule_score,
                "rule_details": [r.to_dict() for r in triggered],
            },
            explanation=explanation,
            metadata={"rule_count": len(_ALL_RULES)},
        )

    def _run_rules(
        self, features: Dict[str, Any], df: Optional[pd.DataFrame]
    ) -> List[RuleResult]:
        """Runs all rules against a single customer's feature dict."""
        results = []
        for rule in _ALL_RULES:
            if rule.is_enabled():
                result = rule.evaluate(features, df)
                results.append(result)
        return results

    def _run_global_rules(
        self, all_features: Dict[str, Dict[str, Any]], df: Optional[pd.DataFrame]
    ) -> List[RuleResult]:
        """
        Runs rules across all customers in global mode.
        Returns aggregated results for the worst-scoring customers.
        """
        all_results: List[RuleResult] = []
        customer_scores: Dict[str, float] = {}

        for customer_id, features in all_features.items():
            customer_df = (
                df[df["sender_id"] == customer_id] if df is not None else None
            )
            cust_results = self._run_rules(features, customer_df)
            triggered = [r for r in cust_results if r.triggered]
            score = min(100.0, sum(r.score for r in triggered))
            if score > 0:
                customer_scores[customer_id] = score
                all_results.extend(triggered)

        # Deduplicate by rule name — report unique triggered rules
        seen: set = set()
        unique_results = []
        for r in all_results:
            if r.rule_name not in seen:
                seen.add(r.rule_name)
                unique_results.append(r)

        # Store top suspicious customers in context
        top_suspicious = sorted(customer_scores.items(), key=lambda x: -x[1])[:20]
        context_ref = None  # Cannot reference context here; stored by caller
        return unique_results
