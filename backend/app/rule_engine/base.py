"""
Rule Engine: BaseRule

Abstract base class for all AML detection rules.
Each rule is fully independent, reads its config from rules.yaml,
and returns a standardised RuleResult.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from app.logging.logger import get_logger

logger = get_logger(__name__)

_CONFIG_PATH = Path(__file__).parent.parent / "config" / "rules.yaml"


def load_rules_config() -> Dict[str, Any]:
    """Loads the rules.yaml configuration file once at import time."""
    if not _CONFIG_PATH.exists():
        logger.warning("rules_config_missing", path=str(_CONFIG_PATH))
        return {}
    with open(_CONFIG_PATH, "r") as f:
        return yaml.safe_load(f) or {}


# Module-level config cache
_RULES_CONFIG: Dict[str, Any] = load_rules_config()


@dataclass
class RuleResult:
    """
    Standardised output returned by every AML rule.

    All fields are required — rules must always explain their decision,
    even when they produce a score of 0 (i.e. not triggered).
    """
    rule_name: str
    triggered: bool
    score: float                            # 0–100 contribution to composite risk
    confidence: float                       # 0–1 model confidence
    reason: str                             # Human-readable explanation
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    affected_transactions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_name": self.rule_name,
            "triggered": self.triggered,
            "score": self.score,
            "confidence": self.confidence,
            "reason": self.reason,
            "evidence": self.evidence,
            "affected_transactions": self.affected_transactions,
        }


class BaseRule(ABC):
    """
    Abstract base class for all AML detection rules.

    Subclasses implement evaluate() with their specific detection logic.
    Configuration is loaded from rules.yaml by key name.
    """

    def __init__(self) -> None:
        self._config = _RULES_CONFIG.get(self.config_key, {})
        if not self._config:
            logger.warning("rule_config_missing", rule=self.name, key=self.config_key)

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable rule name."""

    @property
    @abstractmethod
    def config_key(self) -> str:
        """Key in rules.yaml for this rule's configuration."""

    @abstractmethod
    def evaluate(
        self,
        features: Dict[str, Any],
        transactions_df: Optional[Any] = None,
    ) -> RuleResult:
        """
        Evaluates the rule against feature vectors and raw transactions.

        Args:
            features: Computed AML feature dictionary for the entity.
            transactions_df: Optional raw DataFrame for evidence extraction.

        Returns:
            A fully populated RuleResult.
        """

    def is_enabled(self) -> bool:
        """Returns False if the rule is disabled in configuration."""
        return bool(self._config.get("enabled", True))

    def get_cfg(self, key: str, default: Any = None) -> Any:
        """Type-safe config value accessor."""
        return self._config.get(key, default)
