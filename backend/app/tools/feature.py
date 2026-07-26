"""
Tool: FeatureTool (Production Implementation)

Delegates all computation to FeatureService. Stores results in ExecutionContext.
Never recomputes features already cached.
"""
from app.constants import ToolName
from app.interfaces.tools import BaseTool
from app.schemas.execution_context import ExecutionContext
from app.schemas.tool_result import ToolResult
from app.services.dataset import DatasetService
from app.services.feature import FeatureService

_FEATURE_CACHE_KEY = "features_df"
_CUSTOMER_FEATURE_KEY = "customer_features"


class FeatureTool(BaseTool):
    """Computes AML behavioural features from the cached transaction DataFrame."""

    def __init__(self, feature_service: FeatureService) -> None:
        self._service = feature_service

    @property
    def name(self) -> str:
        return ToolName.FEATURE

    @property
    def description(self) -> str:
        return (
            "Computes 18 AML behavioural features: velocity, rolling sums, "
            "structuring ratios, cross-border activity, beneficiary diversity, "
            "rapid cash-out score, dormant days, and temporal patterns."
        )

    async def _run(self, context: ExecutionContext) -> ToolResult:
        # Dependency check
        if not context.get_var("dataset_loaded"):
            return ToolResult.failure(
                self.name,
                "DatasetTool must run before FeatureTool. 'dataset_loaded' not set in context."
            )

        # Return cached features if already computed
        cached_features = context.get_cached_features("features")
        if cached_features is not None:
            global_df = context.get_df(_FEATURE_CACHE_KEY)
            return ToolResult(
                success=True,
                status="completed",
                tool_name=self.name,
                execution_time_ms=0.0,
                confidence=1.0,
                data={"feature_count": 18, "customers_profiled": len(global_df) if global_df is not None else 1, "source": "cache"},
                explanation="Feature vectors returned from cache.",
                metadata={"cached": True},
            )

        df = context.get_df(DatasetService.DF_TRANSACTIONS)
        if df is None or df.empty:
            return ToolResult.failure(self.name, "Transaction DataFrame is empty — nothing to compute features on.")

        customer_id = context.get_var("filter_customer_id")

        if customer_id:
            # Single customer mode
            cust_df = df[df["sender_id"] == customer_id]
            features = self._service.compute_customer_features(customer_id, cust_df)
            context.set_var(_CUSTOMER_FEATURE_KEY, features)
            context.set_var("features", features)
            context.set_cached_features("features", features)

            return ToolResult(
                success=True,
                status="completed",
                tool_name=self.name,
                execution_time_ms=0.0,
                confidence=1.0,
                data={
                    "customer_id": customer_id,
                    "feature_count": len(features),
                    "features": features,
                },
                explanation=(
                    f"Computed {len(features)} AML features for customer {customer_id}. "
                    f"Transaction count: {features.get('transaction_count', 0)}."
                ),
                metadata={"mode": "single_customer"},
            )
        else:
            # Global mode — profile all customers
            global_feature_df = self._service.compute_global_features(df)
            context.set_df(_FEATURE_CACHE_KEY, global_feature_df)
            # Store as dict for downstream rule/ML tools
            features_dict = global_feature_df.to_dict(orient="index") if not global_feature_df.empty else {}
            context.set_var("features", features_dict)
            context.set_cached_features("features", features_dict)

            return ToolResult(
                success=True,
                status="completed",
                tool_name=self.name,
                execution_time_ms=0.0,
                confidence=1.0,
                data={
                    "customers_profiled": len(global_feature_df),
                    "feature_count": 18,
                    "top_velocity": (
                        float(global_feature_df["velocity_per_day"].max())
                        if not global_feature_df.empty and "velocity_per_day" in global_feature_df.columns
                        else 0.0
                    ),
                },
                explanation=(
                    f"Computed 18 AML features for {len(global_feature_df)} customers."
                ),
                metadata={"mode": "global", "feature_count": 18},
            )
