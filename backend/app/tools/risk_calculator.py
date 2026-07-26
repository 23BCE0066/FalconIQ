"""
Tool: RiskCalculatorTool (Production Implementation)

Computes composite risk score by delegating to RiskService.
Fetches real customer profile data and blends it with live rule, ML,
and behavioural feature scores.
"""
from typing import Any, Dict

from app.constants import KYCStatus, RiskLevel, ToolName
from app.interfaces.tools import BaseTool
from app.schemas.execution_context import ExecutionContext
from app.schemas.tool_result import ToolResult
from app.services.dataset import DatasetService
from app.services.risk import RiskService


class RiskCalculatorTool(BaseTool):
    """Computes a composite 0–100 risk score using weighted inputs."""

    def __init__(
        self, risk_service: RiskService, dataset_service: DatasetService
    ) -> None:
        self._risk_service = risk_service
        self._dataset_service = dataset_service

    @property
    def name(self) -> str:
        return ToolName.RISK_CALCULATOR

    @property
    def description(self) -> str:
        return (
            "Computes a composite risk score (0–100) combining rule scores, "
            "ML anomaly scores, and customer KYC/profile risk. "
            "Produces a LOW/MEDIUM/HIGH/CRITICAL risk classification."
        )

    async def _run(self, context: ExecutionContext) -> ToolResult:
        rule_score = context.get_var("rule_score", 0.0)
        ml_score = context.get_var("ml_score", 0.0)
        
        customer_id = context.get_var("filter_customer_id")
        kyc_status = KYCStatus.PENDING
        customer_risk = RiskLevel.LOW
        
        # Load real customer profile if specific customer was requested
        if customer_id:
            customer = self._dataset_service.get_customer(customer_id)
            if customer:
                kyc_status = customer.kyc_status
                customer_risk = customer.risk_category

        # Features could be a dict (single) or a nested dict (global).
        features = context.get_var("features", {})
        if isinstance(features, dict) and customer_id and customer_id in features:
            # global mode but we have a customer
            cust_features = features[customer_id]
        elif isinstance(features, dict) and "transaction_count" in features:
            # single customer mode
            cust_features = features
        else:
            cust_features = {}

        triggered_rules = context.get_var("triggered_rules", [])

        result = self._risk_service.score_and_classify(
            kyc_status=kyc_status,
            customer_risk=customer_risk,
            rule_score=rule_score,
            ml_score=ml_score,
            features=cust_features,
            triggered_rules=triggered_rules,
            tool_confidence=0.95
        )

        score = float(result["risk_score"])
        level = result["risk_level"]

        context.set_var("risk_score", score)
        context.set_var("risk_level", level.value)
        context.set_var("risk_components", result["evidence"])

        return ToolResult(
            success=True,
            status="completed",
            tool_name=self.name,
            execution_time_ms=0.0,
            confidence=result["confidence"],
            data={
                "risk_score": score,
                "risk_level": level.value,
                "confidence": result["confidence"],
                "triggered_rules": result["triggered_rules"],
                "top_contributors": result["top_contributors"],
                "recommendation": result["recommendation"],
                "evidence": result["evidence"],
                "profile_used": bool(customer_id and customer),
            },
            explanation=(
                f"Composite risk score computed: {score:.1f}/100 → {level.value}. "
                f"Top contributors: {', '.join(result['top_contributors'])}. "
                f"Recommendation: {result['recommendation']}"
            ),
            metadata={"scoring_model": "weighted_composite_production"},
        )
