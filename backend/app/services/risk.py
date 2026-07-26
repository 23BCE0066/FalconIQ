"""
Service: RiskService (Production Implementation)

Computes composite risk scores by blending multiple risk dimensions:
- KYC Status and baseline Customer Risk
- Rule Engine scores
- ML Anomaly scores
- Behavioural features risk
- Country risk

The risk formula is configurable via rules.yaml.
"""
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from app.constants import KYCStatus, RiskLevel
from app.interfaces.services import BaseService
from app.logging.logger import get_logger

logger = get_logger(__name__)

_CONFIG_PATH = Path(__file__).parent.parent / "config" / "rules.yaml"


def load_risk_weights() -> Dict[str, float]:
    """Loads risk weights from rules.yaml."""
    default_weights = {
        "kyc": 0.15,
        "rule": 0.45,
        "ml": 0.25,
        "features": 0.10,
        "country": 0.05,
    }
    if not _CONFIG_PATH.exists():
        return default_weights
    try:
        with open(_CONFIG_PATH, "r") as f:
            cfg = yaml.safe_load(f) or {}
            weights = cfg.get("risk", {}).get("weights", default_weights)
            # Normalize to 1.0 just in case
            total = sum(weights.values())
            if total > 0:
                return {k: v / total for k, v in weights.items()}
            return default_weights
    except Exception:
        logger.warning("failed_to_load_risk_weights")
        return default_weights


KYC_SCORE_MAP = {
    KYCStatus.VERIFIED: 10.0,
    KYCStatus.PENDING: 40.0,
    KYCStatus.FAILED: 90.0,
    KYCStatus.EXPIRED: 70.0,
}

RISK_LEVEL_SCORE_MAP = {
    RiskLevel.LOW: 20.0,
    RiskLevel.MEDIUM: 50.0,
    RiskLevel.HIGH: 80.0,
    RiskLevel.CRITICAL: 100.0,
}

RISK_THRESHOLDS = {
    RiskLevel.LOW: (0.0, 35.0),
    RiskLevel.MEDIUM: (35.0, 65.0),
    RiskLevel.HIGH: (65.0, 85.0),
    RiskLevel.CRITICAL: (85.0, 100.0),
}


class RiskService(BaseService):
    """
    Computes composite risk scores using configurable weighted components.
    """

    def __init__(self, weights: Optional[Dict[str, float]] = None) -> None:
        self._weights = weights or load_risk_weights()

    def compute_composite_score(
        self,
        kyc_status: KYCStatus,
        customer_risk: RiskLevel,
        rule_score: float,
        ml_score: float,
        behaviour_score: float,
        country_score: float,
    ) -> float:
        """
        Computes a normalized 0–100 composite risk score based on configured weights.
        """
        # KYC component: blends KYC status with customer profile risk
        kyc_raw = KYC_SCORE_MAP.get(kyc_status, 40.0)
        profile_raw = RISK_LEVEL_SCORE_MAP.get(customer_risk, 20.0)
        s_kyc = (kyc_raw + profile_raw) / 2.0

        score = (
            self._weights.get("kyc", 0.0) * s_kyc
            + self._weights.get("rule", 0.0) * rule_score
            + self._weights.get("ml", 0.0) * ml_score
            + self._weights.get("features", 0.0) * behaviour_score
            + self._weights.get("country", 0.0) * country_score
        )
        return round(min(100.0, max(0.0, score)), 2)

    def classify_risk(self, score: float) -> RiskLevel:
        """Classifies a numeric risk score into a RiskLevel enum value."""
        for level, (low, high) in RISK_THRESHOLDS.items():
            if low <= score <= high:  # Using <= for upper bound safely
                if level != RiskLevel.CRITICAL and score == high:
                    continue # Edge case, let it bump to next bucket if exactly on boundary except for 100
                return level
        return RiskLevel.CRITICAL

    def score_and_classify(
        self,
        kyc_status: KYCStatus,
        customer_risk: RiskLevel,
        rule_score: float,
        ml_score: float,
        features: Dict[str, Any],
        triggered_rules: List[str] = None,
        tool_confidence: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Computes the score and returns detailed components.
        Extracts behaviour and country scores from features.
        """
        if triggered_rules is None:
            triggered_rules = []

        # Base behaviour risk (velocity, dormancy, cash-out)
        vel = float(features.get("velocity_per_day", 0.0))
        cashout = float(features.get("rapid_cashout_score", 0.0))
        dormant = float(features.get("dormant_days", 0.0))
        
        # Max behavior proxy: cap at 100
        behaviour_score = min(100.0, (vel * 2) + (cashout * 100) + (dormant / 3.0))
        
        # Country risk
        hr_count = int(features.get("high_risk_country_count", 0))
        cross_border = float(features.get("cross_border_ratio", 0.0))
        country_score = min(100.0, (hr_count * 50) + (cross_border * 50))

        kyc_raw = KYC_SCORE_MAP.get(kyc_status, 40.0)
        profile_raw = RISK_LEVEL_SCORE_MAP.get(customer_risk, 20.0)
        s_kyc = (kyc_raw + profile_raw) / 2.0

        components = {
            "kyc": s_kyc * self._weights.get("kyc", 0.0),
            "rule": rule_score * self._weights.get("rule", 0.0),
            "ml": ml_score * self._weights.get("ml", 0.0),
            "features": behaviour_score * self._weights.get("features", 0.0),
            "country": country_score * self._weights.get("country", 0.0),
        }

        score = self.compute_composite_score(
            kyc_status, customer_risk, rule_score, ml_score, behaviour_score, country_score
        )
        level = self.classify_risk(score)
        
        top_contributors = sorted(components.items(), key=lambda x: x[1], reverse=True)[:2]
        top_contributors = [k for k, v in top_contributors if v > 0]

        recommendation = "No action required."
        if level == RiskLevel.CRITICAL:
            recommendation = "Immediate account freeze and SAR filing recommended."
        elif level == RiskLevel.HIGH:
            recommendation = "Manual review required by L2 compliance."
        elif level == RiskLevel.MEDIUM:
            recommendation = "Monitor activity."

        return {
            "risk_score": score,
            "risk_level": level,
            "confidence": tool_confidence,
            "triggered_rules": triggered_rules,
            "top_contributors": top_contributors,
            "recommendation": recommendation,
            "evidence": {
                "kyc_score": kyc_raw,
                "profile_risk": profile_raw,
                "rule_score": rule_score,
                "ml_score": ml_score,
                "behaviour_score": round(behaviour_score, 2),
                "country_score": round(country_score, 2),
                "weights_used": self._weights,
            },
        }
