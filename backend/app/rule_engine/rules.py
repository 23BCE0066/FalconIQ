"""
Rule: StructuringRule

Detects structuring (smurfing) — repeated transactions just below
the cash reporting threshold, designed to evade regulatory reporting.

FATF Reference: Typology 1 — Structuring / Smurfing
FinCEN Threshold: $10,000 USD
"""
from typing import Any, Dict, List, Optional

import pandas as pd

from app.rule_engine.base import BaseRule, RuleResult


class StructuringRule(BaseRule):
    """
    Fires when a customer has multiple near-miss transactions below the
    reporting threshold within the configured time window.
    """

    @property
    def name(self) -> str:
        return "StructuringRule"

    @property
    def config_key(self) -> str:
        return "structuring"

    def evaluate(
        self,
        features: Dict[str, Any],
        transactions_df: Optional[Any] = None,
    ) -> RuleResult:
        if not self.is_enabled():
            return RuleResult(
                rule_name=self.name, triggered=False, score=0.0, confidence=0.0,
                reason="Rule is disabled in configuration."
            )

        min_count: int = self.get_cfg("min_count", 3)
        threshold: float = self.get_cfg("threshold", 10_000.0)
        near_miss_ratio: float = self.get_cfg("near_miss_ratio", 0.95)
        score_value: float = self.get_cfg("score", 70.0)
        confidence: float = self.get_cfg("confidence", 0.85)

        structuring_count = int(features.get("structuring_count", 0))
        triggered = structuring_count >= min_count

        evidence: List[Dict[str, Any]] = []
        affected: List[str] = []

        if triggered and transactions_df is not None:
            try:
                lo = threshold * near_miss_ratio
                near_miss_txs = transactions_df[
                    (transactions_df["amount"] >= lo)
                    & (transactions_df["amount"] < threshold)
                ]
                for _, row in near_miss_txs.head(10).iterrows():
                    evidence.append({
                        "transaction_id": str(row.get("transaction_id", "")),
                        "amount": float(row["amount"]),
                        "timestamp": str(row["timestamp"]),
                    })
                    affected.append(str(row.get("transaction_id", "")))
            except Exception:
                pass

        reason = (
            f"Detected {structuring_count} transactions between "
            f"${threshold * near_miss_ratio:,.0f} and ${threshold:,.0f} "
            f"(threshold: {min_count})."
            if triggered
            else f"Only {structuring_count} near-miss transactions found (minimum: {min_count})."
        )

        return RuleResult(
            rule_name=self.name,
            triggered=triggered,
            score=score_value if triggered else 0.0,
            confidence=confidence if triggered else 0.0,
            reason=reason,
            evidence=evidence,
            affected_transactions=affected,
        )


class VelocityRule(BaseRule):
    """
    Fires when transaction velocity (frequency or total amount) exceeds
    configured thresholds within a rolling time window.
    """

    @property
    def name(self) -> str:
        return "VelocityRule"

    @property
    def config_key(self) -> str:
        return "velocity"

    def evaluate(
        self,
        features: Dict[str, Any],
        transactions_df: Optional[Any] = None,
    ) -> RuleResult:
        if not self.is_enabled():
            return RuleResult(
                rule_name=self.name, triggered=False, score=0.0, confidence=0.0,
                reason="Rule is disabled."
            )

        max_per_day: float = self.get_cfg("max_tx_per_day", 15.0)
        max_amount: float = self.get_cfg("max_amount_window", 500_000.0)
        score_value: float = self.get_cfg("score", 60.0)
        confidence: float = self.get_cfg("confidence", 0.80)

        velocity = float(features.get("velocity_per_day", 0.0))
        rolling_sum = float(features.get("rolling_sum_30d", 0.0))

        velocity_breach = velocity > max_per_day
        amount_breach = rolling_sum > max_amount
        triggered = velocity_breach or amount_breach

        reasons = []
        if velocity_breach:
            reasons.append(f"velocity {velocity:.1f} tx/day > limit {max_per_day}")
        if amount_breach:
            reasons.append(f"rolling sum ${rolling_sum:,.0f} > limit ${max_amount:,.0f}")

        reason = (
            "High transaction velocity: " + "; ".join(reasons)
            if triggered
            else f"Normal velocity ({velocity:.2f} tx/day, ${rolling_sum:,.0f} rolling sum)."
        )

        return RuleResult(
            rule_name=self.name,
            triggered=triggered,
            score=score_value if triggered else 0.0,
            confidence=confidence if triggered else 0.0,
            reason=reason,
            evidence=[{"velocity_per_day": velocity, "rolling_sum_30d": rolling_sum}],
        )


class RapidCashOutRule(BaseRule):
    """
    Detects rapid cash-out behaviour — high outgoing cash-out volume
    relative to total transaction flow.
    """

    @property
    def name(self) -> str:
        return "RapidCashOutRule"

    @property
    def config_key(self) -> str:
        return "rapid_cashout"

    def evaluate(
        self,
        features: Dict[str, Any],
        transactions_df: Optional[Any] = None,
    ) -> RuleResult:
        if not self.is_enabled():
            return RuleResult(
                rule_name=self.name, triggered=False, score=0.0, confidence=0.0,
                reason="Rule is disabled."
            )

        cashout_ratio_threshold: float = self.get_cfg("cashout_ratio", 0.85)
        score_value: float = self.get_cfg("score", 75.0)
        confidence: float = self.get_cfg("confidence", 0.88)

        cashout_score = float(features.get("rapid_cashout_score", 0.0))
        triggered = cashout_score >= cashout_ratio_threshold

        reason = (
            f"Rapid cash-out score {cashout_score:.2%} exceeds threshold {cashout_ratio_threshold:.0%}."
            if triggered
            else f"Cash-out ratio {cashout_score:.2%} within normal range."
        )

        return RuleResult(
            rule_name=self.name,
            triggered=triggered,
            score=score_value if triggered else 0.0,
            confidence=confidence if triggered else 0.0,
            reason=reason,
            evidence=[{"rapid_cashout_score": cashout_score}],
        )


class LayeringRule(BaseRule):
    """
    Detects layering — unusually high number of unique counterparties
    combined with high cross-border activity indicating fund movement obfuscation.
    """

    @property
    def name(self) -> str:
        return "LayeringRule"

    @property
    def config_key(self) -> str:
        return "layering"

    def evaluate(
        self,
        features: Dict[str, Any],
        transactions_df: Optional[Any] = None,
    ) -> RuleResult:
        if not self.is_enabled():
            return RuleResult(
                rule_name=self.name, triggered=False, score=0.0, confidence=0.0,
                reason="Rule is disabled."
            )

        min_hops: int = self.get_cfg("min_hops", 3)
        min_total: float = self.get_cfg("min_total_amount", 50_000.0)
        score_value: float = self.get_cfg("score", 80.0)
        confidence: float = self.get_cfg("confidence", 0.78)

        unique_receivers = int(features.get("unique_receivers", 0))
        cross_border_ratio = float(features.get("cross_border_ratio", 0.0))
        total_amount = float(features.get("total_amount", 0.0))

        # Layering proxy: many distinct receivers + cross-border + large volume
        triggered = (
            unique_receivers >= min_hops
            and cross_border_ratio > 0.30
            and total_amount >= min_total
        )

        reason = (
            f"Layering pattern: {unique_receivers} unique receivers, "
            f"{cross_border_ratio:.0%} cross-border, ${total_amount:,.0f} total."
            if triggered
            else "No significant layering indicators detected."
        )

        return RuleResult(
            rule_name=self.name,
            triggered=triggered,
            score=score_value if triggered else 0.0,
            confidence=confidence if triggered else 0.0,
            reason=reason,
            evidence=[{
                "unique_receivers": unique_receivers,
                "cross_border_ratio": cross_border_ratio,
                "total_amount": total_amount,
            }],
        )


class CrossBorderRule(BaseRule):
    """
    Detects suspicious cross-border transfer activity involving high-risk countries.
    """

    @property
    def name(self) -> str:
        return "CrossBorderRule"

    @property
    def config_key(self) -> str:
        return "cross_border"

    def evaluate(
        self,
        features: Dict[str, Any],
        transactions_df: Optional[Any] = None,
    ) -> RuleResult:
        if not self.is_enabled():
            return RuleResult(
                rule_name=self.name, triggered=False, score=0.0, confidence=0.0,
                reason="Rule is disabled."
            )

        min_ratio: float = self.get_cfg("min_ratio", 0.60)
        min_hr_count: int = self.get_cfg("min_high_risk_count", 2)
        score_value: float = self.get_cfg("score", 55.0)
        confidence: float = self.get_cfg("confidence", 0.75)

        cross_border_ratio = float(features.get("cross_border_ratio", 0.0))
        hr_count = int(features.get("high_risk_country_count", 0))

        triggered = cross_border_ratio >= min_ratio or hr_count >= min_hr_count

        reason = (
            f"Cross-border: {cross_border_ratio:.0%} transactions are international; "
            f"{hr_count} involve high-risk jurisdictions."
            if triggered
            else f"Cross-border activity normal ({cross_border_ratio:.0%}, {hr_count} high-risk)."
        )

        return RuleResult(
            rule_name=self.name,
            triggered=triggered,
            score=score_value if triggered else 0.0,
            confidence=confidence if triggered else 0.0,
            reason=reason,
            evidence=[{
                "cross_border_ratio": cross_border_ratio,
                "high_risk_country_count": hr_count,
            }],
        )


class DormantAccountRule(BaseRule):
    """
    Detects dormant account reactivation — sudden large transaction activity
    after a long period of inactivity.
    """

    @property
    def name(self) -> str:
        return "DormantAccountRule"

    @property
    def config_key(self) -> str:
        return "dormant_account"

    def evaluate(
        self,
        features: Dict[str, Any],
        transactions_df: Optional[Any] = None,
    ) -> RuleResult:
        if not self.is_enabled():
            return RuleResult(
                rule_name=self.name, triggered=False, score=0.0, confidence=0.0,
                reason="Rule is disabled."
            )

        min_dormant: int = self.get_cfg("min_dormant_days", 180)
        min_amount: float = self.get_cfg("min_reactivation_amount", 5_000.0)
        score_value: float = self.get_cfg("score", 65.0)
        confidence: float = self.get_cfg("confidence", 0.82)

        dormant_days = int(features.get("dormant_days", 0))
        max_amount = float(features.get("max_amount", 0.0))

        triggered = dormant_days >= min_dormant and max_amount >= min_amount

        reason = (
            f"Dormant account reactivated: {dormant_days} days inactive, "
            f"reactivating transaction ${max_amount:,.0f}."
            if triggered
            else f"No dormant account pattern ({dormant_days} days, ${max_amount:,.0f} max tx)."
        )

        return RuleResult(
            rule_name=self.name,
            triggered=triggered,
            score=score_value if triggered else 0.0,
            confidence=confidence if triggered else 0.0,
            reason=reason,
            evidence=[{"dormant_days": dormant_days, "max_reactivation_amount": max_amount}],
        )
