"""
Tool: MLEngineTool (Production Implementation)

Applies unsupervised anomaly detection (Isolation Forest) by delegating
to MLService. Requires FeatureTool to have cached features.
"""
from typing import Any, Dict

import pandas as pd

from app.constants import ToolName
from app.interfaces.tools import BaseTool
from app.schemas.execution_context import ExecutionContext
from app.schemas.tool_result import ToolResult
from app.services.ml import MLService

_FEATURE_CACHE_KEY = "features_df"


class MLEngineTool(BaseTool):
    """
    Applies Machine Learning anomaly detection on the computed feature vectors.
    """

    def __init__(self, ml_service: MLService) -> None:
        self._service = ml_service

    @property
    def name(self) -> str:
        return ToolName.ML_ENGINE

    @property
    def description(self) -> str:
        return (
            "Applies unsupervised ML anomaly detection using Isolation Forest. "
            "Returns anomaly scores per entity. Requires feature tool output."
        )

    async def _run(self, context: ExecutionContext) -> ToolResult:
        customer_id = context.get_var("filter_customer_id")
        
        # If we have a global feature DataFrame, we can run IF properly
        features_df: pd.DataFrame | None = context.get_df(_FEATURE_CACHE_KEY)
        
        if features_df is None or features_df.empty:
            # If in single customer mode without global batch, we can't train IF well.
            # But for completeness, if we only have one customer's features, we fallback.
            features = context.get_var("features")
            if not features:
                return ToolResult.failure(self.name, "Feature vector not found in context.")
            
            if isinstance(features, dict) and customer_id:
                # Mock a 0 score since we can't detect anomalies on N=1
                context.set_var("ml_score", 0.0)
                return ToolResult(
                    success=True,
                    status="completed",
                    tool_name=self.name,
                    execution_time_ms=0.0,
                    confidence=0.5,
                    data={
                        "model": "IsolationForest",
                        "anomalies_detected": 0,
                        "ml_score": 0.0,
                        "note": "Requires global dataset for Isolation Forest. Falling back to 0 score for single customer."
                    },
                    explanation="Insufficient data for Isolation Forest. ML score set to 0.",
                )
            else:
                return ToolResult.failure(self.name, "Invalid feature format for ML Engine.")

        # Run Isolation Forest on the batch
        scores_dict, top_anomalies = self._service.detect_anomalies(features_df)
        
        anomalies_count = len(top_anomalies)
        
        if customer_id:
            # Single customer focus, but evaluated against the batch
            score = scores_dict.get(customer_id, 0.0)
            context.set_var("ml_score", score)
            
            return ToolResult(
                success=True,
                status="completed",
                tool_name=self.name,
                execution_time_ms=0.0,
                confidence=0.85,
                data={
                    "model": "IsolationForest",
                    "customer_id": customer_id,
                    "ml_score": score,
                    "anomalies_in_batch": anomalies_count,
                    "contamination": self._service.contamination,
                },
                explanation=(
                    f"Isolation Forest applied to batch of {len(features_df)} customers. "
                    f"Customer {customer_id} received anomaly score {score:.1f}/100."
                ),
            )
        else:
            # Global focus
            max_score = max(scores_dict.values()) if scores_dict else 0.0
            context.set_var("ml_scores_dict", scores_dict)
            
            return ToolResult(
                success=True,
                status="completed",
                tool_name=self.name,
                execution_time_ms=0.0,
                confidence=0.85,
                data={
                    "model": "IsolationForest",
                    "anomalies_detected": anomalies_count,
                    "max_anomaly_score": max_score,
                    "top_anomalies": top_anomalies,
                    "contamination": self._service.contamination,
                },
                explanation=(
                    f"Isolation Forest applied. Detected {anomalies_count} anomalies "
                    f"out of {len(features_df)} customers. Max score: {max_score:.1f}."
                ),
            )
