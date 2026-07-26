"""
Service: MLService

Provides unsupervised machine learning capabilities for AML anomaly detection.
Uses Isolation Forest to detect multivariate outliers in the feature space.
"""
from typing import Any, Dict, List, Tuple

import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from app.interfaces.services import BaseService
from app.logging.logger import get_logger

logger = get_logger(__name__)

# Features to exclude from ML training (identifiers, target variables)
_EXCLUDED_FEATURES = {
    "customer_id",
    "transaction_count",  # Often correlates too strongly with raw volume
}


class MLService(BaseService):
    """
    Machine Learning service for AML pattern detection.
    Currently implements unsupervised Isolation Forest for anomaly detection.
    """

    def __init__(self, contamination: float = 0.05, random_state: int = 42) -> None:
        self.contamination = contamination
        self.random_state = random_state

    def detect_anomalies(
        self, features_df: pd.DataFrame
    ) -> Tuple[Dict[str, float], List[Dict[str, Any]]]:
        """
        Runs Isolation Forest on a batch of customer feature vectors.

        Args:
            features_df: DataFrame containing computed features per customer.
                         Index should be customer_id or contain it as a column.

        Returns:
            Tuple of:
            1. Dictionary mapping customer_id -> anomaly_score (0.0 to 100.0)
            2. List of top anomalous customer details for reporting
        """
        if features_df.empty or len(features_df) < 5:
            logger.warning("ml_service_too_few_samples", count=len(features_df))
            return {}, []

        # Prepare data
        df = features_df.copy()
        if "customer_id" in df.columns:
            df = df.set_index("customer_id")

        # Select numeric columns, dropping excluded ones
        numeric_cols = df.select_dtypes(include=["number"]).columns
        train_cols = [c for c in numeric_cols if c not in _EXCLUDED_FEATURES]

        if not train_cols:
            return {}, []

        X = df[train_cols].fillna(0)

        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # Train & Predict Isolation Forest
        model = IsolationForest(
            contamination=self.contamination, random_state=self.random_state
        )
        model.fit(X_scaled)
        
        # decision_function returns negative values for outliers, positive for inliers
        # We invert and normalize this to a 0-100 anomaly score where 100 is most anomalous.
        scores_raw = -model.decision_function(X_scaled)
        
        # Normalize to 0-100 based on min/max of the batch
        min_score, max_score = scores_raw.min(), scores_raw.max()
        range_score = max_score - min_score if max_score > min_score else 1.0
        
        normalized_scores = ((scores_raw - min_score) / range_score) * 100.0
        
        # Predictions: -1 for outlier, 1 for inlier
        predictions = model.predict(X_scaled)
        
        df["anomaly_score"] = normalized_scores
        df["is_outlier"] = predictions == -1

        results_dict: Dict[str, float] = {}
        for cust_id, row in df.iterrows():
            results_dict[str(cust_id)] = float(row["anomaly_score"])

        # Extract top anomalies
        outliers = df[df["is_outlier"]].sort_values("anomaly_score", ascending=False)
        
        top_anomalies: List[Dict[str, Any]] = []
        for cust_id, row in outliers.head(10).iterrows():
            top_anomalies.append({
                "customer_id": str(cust_id),
                "anomaly_score": round(float(row["anomaly_score"]), 2),
                "key_features": {
                    "total_amount": float(row.get("total_amount", 0.0)),
                    "velocity_per_day": float(row.get("velocity_per_day", 0.0)),
                    "cross_border_ratio": float(row.get("cross_border_ratio", 0.0))
                }
            })

        logger.info(
            "ml_anomaly_detection_complete",
            samples=len(X),
            outliers_detected=len(outliers)
        )

        return results_dict, top_anomalies
