"""
Service: FeatureService (Production Implementation)

Computes the complete AML behavioural feature vector from transaction DataFrames.
Follows FATF typology guidelines for financial crime pattern detection.

All 18 features are computed here. Tools never compute features themselves.
Feature results are stored in ExecutionContext by FeatureTool.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from app.interfaces.services import BaseService
from app.logging.logger import get_logger

logger = get_logger(__name__)

# Country risk tiers — can be moved to config/rules.yaml in production
HIGH_RISK_COUNTRIES = {
    "AFG", "DZA", "AGO", "BGD", "BLR", "MMR", "CMR", "CAF", "TCD",
    "COD", "CUB", "ERI", "ETH", "GIN", "GNB", "HTI", "IRN", "IRQ",
    "PRK", "LBY", "MLI", "MOZ", "NGA", "PAK", "PAN", "RUS", "SOM",
    "SSD", "SDN", "SYR", "TZA", "TTO", "UGA", "VEN", "YEM", "ZWE",
}

# Structuring constants
STRUCTURING_THRESHOLD = 10_000.0
STRUCTURING_NEAR_MISS_RATIO = 0.95


class FeatureService(BaseService):
    """
    Computes a comprehensive AML feature vector from transaction DataFrames.

    Features cover: volume, velocity, structuring, temporal behaviour,
    cross-border activity, beneficiary diversity, and cash-flow patterns.
    """

    def compute_customer_features(
        self, customer_id: str, df: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Computes all 18 AML features for a single customer's transactions.

        Args:
            customer_id: The customer being profiled.
            df: DataFrame of this customer's outgoing transactions.

        Returns:
            Dictionary mapping feature name → computed value.
        """
        if df.empty:
            logger.warning("feature_empty_df", customer_id=customer_id)
            return self._empty_features()

        df = df.copy()
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        df = df.sort_values("timestamp")
        now = pd.Timestamp.now(tz="UTC")

        feats: Dict[str, Any] = {}

        # ── 1. Volume Features ─────────────────────────────────────────────────
        feats["transaction_count"] = int(len(df))
        feats["avg_amount"] = round(float(df["amount"].mean()), 2)
        feats["median_amount"] = round(float(df["amount"].median()), 2)
        feats["max_amount"] = round(float(df["amount"].max()), 2)
        feats["total_amount"] = round(float(df["amount"].sum()), 2)
        feats["std_amount"] = round(float(df["amount"].std(ddof=0)), 2)

        # ── 2. Rolling Window Aggregates (30d) ─────────────────────────────────
        last_30d = df[df["timestamp"] >= now - pd.Timedelta(days=30)]
        feats["rolling_sum_30d"] = round(float(last_30d["amount"].sum()), 2)
        feats["rolling_count_30d"] = int(len(last_30d))

        # ── 3. Transaction Velocity ────────────────────────────────────────────
        if len(df) > 1:
            span_days = (
                df["timestamp"].iloc[-1] - df["timestamp"].iloc[0]
            ).total_seconds() / 86_400.0
            feats["velocity_per_day"] = round(
                len(df) / span_days if span_days > 0 else float(len(df)), 4
            )
        else:
            feats["velocity_per_day"] = float(len(df))

        # ── 4. Average Time Gap Between Transactions ───────────────────────────
        if len(df) > 1:
            gaps = df["timestamp"].diff().dropna().dt.total_seconds() / 3_600.0
            feats["avg_time_gap_hours"] = round(float(gaps.mean()), 2)
        else:
            feats["avg_time_gap_hours"] = 0.0

        # ── 5. Counterparty Diversity ──────────────────────────────────────────
        feats["unique_receivers"] = int(df["receiver_id"].nunique())
        if "sender_id" in df.columns:
            feats["unique_senders"] = int(df["sender_id"].nunique())
        else:
            feats["unique_senders"] = 1

        # ── 6. Cross-Border Activity ───────────────────────────────────────────
        cross = df.get("is_cross_border", pd.Series(dtype=bool))
        if cross.dtype == object:
            cross = cross.astype(bool)
        feats["cross_border_ratio"] = round(
            float(cross.sum()) / len(df) if len(df) > 0 else 0.0, 4
        )

        # ── 7. High-Risk Country Transactions ─────────────────────────────────
        if "country" in df.columns:
            hr_count = df["country"].isin(HIGH_RISK_COUNTRIES).sum()
            feats["high_risk_country_count"] = int(hr_count)
        else:
            feats["high_risk_country_count"] = 0

        # ── 8. Temporal Behaviour ──────────────────────────────────────────────
        feats["night_transactions"] = int(
            df.get("is_night", pd.Series(dtype=bool)).astype(bool).sum()
        )
        feats["weekend_transactions"] = int(
            df.get("is_weekend", pd.Series(dtype=bool)).astype(bool).sum()
        )

        # ── 9. Structuring / Smurfing Indicator ───────────────────────────────
        lo = STRUCTURING_THRESHOLD * STRUCTURING_NEAR_MISS_RATIO
        near_miss = df[(df["amount"] >= lo) & (df["amount"] < STRUCTURING_THRESHOLD)]
        feats["structuring_count"] = int(len(near_miss))

        # ── 10. Rapid Cash-Out Score ───────────────────────────────────────────
        # Proxy: high cash-out volumes relative to incoming within 24h windows
        if "type" in df.columns:
            cash_outs = df[df["type"].isin(["CASH_OUT", "TRANSFER"])]
            feats["rapid_cashout_score"] = round(
                float(cash_outs["amount"].sum()) / max(feats["total_amount"], 1.0), 4
            )
        else:
            feats["rapid_cashout_score"] = 0.0

        # ── 11. Dormant Account Days ───────────────────────────────────────────
        if len(df) > 1:
            first_tx = df["timestamp"].iloc[0]
            last_tx = df["timestamp"].iloc[-1]
            feats["dormant_days"] = int(
                (last_tx - first_tx).total_seconds() / 86_400.0
            )
        else:
            feats["dormant_days"] = 0

        # ── 12. Beneficiary Diversity Index (entropy-based) ───────────────────
        receiver_counts = df["receiver_id"].value_counts(normalize=True)
        if len(receiver_counts) > 1:
            entropy = float(-np.sum(receiver_counts * np.log2(receiver_counts + 1e-10)))
            feats["beneficiary_diversity"] = round(entropy, 4)
        else:
            feats["beneficiary_diversity"] = 0.0

        # ── 13. Incoming vs Outgoing Ratio ────────────────────────────────────
        if "sender_id" in df.columns:
            incoming = df[df["receiver_id"] == customer_id]["amount"].sum()
            outgoing = df[df["sender_id"] == customer_id]["amount"].sum()
            total_flow = incoming + outgoing
            feats["incoming_outgoing_ratio"] = round(
                float(incoming) / float(total_flow) if total_flow > 0 else 0.5, 4
            )
        else:
            feats["incoming_outgoing_ratio"] = 0.0

        logger.debug(
            "features_computed",
            customer_id=customer_id,
            feature_count=len(feats),
            transaction_count=feats["transaction_count"],
        )
        return feats

    def compute_global_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Computes per-customer feature vectors across the full dataset.
        Used for global AML pattern detection (structuring sweep, velocity).

        Returns:
            DataFrame with one row per customer, indexed by sender_id.
        """
        if df.empty:
            return pd.DataFrame()

        feature_rows = []
        for customer_id, group in df.groupby("sender_id"):
            feats = self.compute_customer_features(str(customer_id), group)
            feats["customer_id"] = str(customer_id)
            feature_rows.append(feats)

        if not feature_rows:
            return pd.DataFrame()

        result = pd.DataFrame(feature_rows)
        result = result.set_index("customer_id")
        # Fill NaN from std=0 edge cases
        result = result.fillna(0.0)
        return result

    def _empty_features(self) -> Dict[str, Any]:
        """Returns a zeroed feature dict for customers with no transactions."""
        return {
            "transaction_count": 0,
            "avg_amount": 0.0,
            "median_amount": 0.0,
            "max_amount": 0.0,
            "total_amount": 0.0,
            "std_amount": 0.0,
            "rolling_sum_30d": 0.0,
            "rolling_count_30d": 0,
            "velocity_per_day": 0.0,
            "avg_time_gap_hours": 0.0,
            "unique_receivers": 0,
            "unique_senders": 0,
            "cross_border_ratio": 0.0,
            "high_risk_country_count": 0,
            "night_transactions": 0,
            "weekend_transactions": 0,
            "structuring_count": 0,
            "rapid_cashout_score": 0.0,
            "dormant_days": 0,
            "beneficiary_diversity": 0.0,
            "incoming_outgoing_ratio": 0.0,
        }
