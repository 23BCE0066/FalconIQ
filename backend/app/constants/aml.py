"""
Constants: Tool names and AML pattern identifiers.

Centralised registry of all valid tool names and AML pattern types,
preventing Planner Agent hallucinations from breaking the Tool Registry lookup.
"""
from enum import Enum


class ToolName(str, Enum):
    """Canonical names of all registered tools in the ToolRegistry."""
    DATASET = "dataset"
    EDA = "eda"
    FEATURE = "feature"
    RULE_ENGINE = "rule_engine"
    ML_ENGINE = "ml_engine"
    RISK_CALCULATOR = "risk_calculator"
    EXPLAINER = "explainer"
    REPORT_WRITER = "report_writer"
    NETWORK_ANALYZER = "network_analyzer"


class AMLPattern(str, Enum):
    """AML behavioural patterns this platform detects."""
    STRUCTURING = "STRUCTURING"
    SMURFING = "SMURFING"
    LAYERING = "LAYERING"
    RAPID_CASH_OUT = "RAPID_CASH_OUT"
    CIRCULAR_TRANSACTIONS = "CIRCULAR_TRANSACTIONS"
    HIGH_VELOCITY = "HIGH_VELOCITY"
    CROSS_BORDER_TRANSFER = "CROSS_BORDER_TRANSFER"
    UNUSUAL_AMOUNT_DEVIATION = "UNUSUAL_AMOUNT_DEVIATION"
    DORMANT_ACCOUNT_ACTIVATION = "DORMANT_ACCOUNT_ACTIVATION"
    UNKNOWN = "UNKNOWN"


class PlannerIntent(str, Enum):
    """Intent categories the Planner Agent can resolve."""
    STRUCTURING_DETECTION = "STRUCTURING_DETECTION"
    CUSTOMER_LOOKUP = "CUSTOMER_LOOKUP"
    HIGH_RISK_CUSTOMERS = "HIGH_RISK_CUSTOMERS"
    NETWORK_ANALYSIS = "NETWORK_ANALYSIS"
    EDA_REQUEST = "EDA_REQUEST"
    REPORT_GENERATION = "REPORT_GENERATION"
    GENERAL_INVESTIGATION = "GENERAL_INVESTIGATION"
