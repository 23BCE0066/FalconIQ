"""
Constants: Risk levels, alert statuses, session statuses, tool names, and AML pattern names.

These enums eliminate magic strings throughout the entire codebase and serve as the
single source of truth for domain vocabulary.
"""
from enum import Enum


class RiskLevel(str, Enum):
    """Customer or alert risk classification levels."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AlertStatus(str, Enum):
    """Lifecycle status of a compliance alert."""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    DISMISSED = "DISMISSED"
    UNDER_REVIEW = "UNDER_REVIEW"
    ESCALATED = "ESCALATED"


class KYCStatus(str, Enum):
    """Know Your Customer verification status."""
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"


class SessionStatus(str, Enum):
    """Agent session execution lifecycle."""
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PARTIAL = "PARTIAL"


class DetectionType(str, Enum):
    """Source of a triggered alert."""
    RULE = "RULE"
    ML = "ML"
    HYBRID = "HYBRID"


class TransactionType(str, Enum):
    """Types of financial transactions."""
    TRANSFER = "TRANSFER"
    CASH_IN = "CASH_IN"
    CASH_OUT = "CASH_OUT"
    PAYMENT = "PAYMENT"
    DEBIT = "DEBIT"
    CREDIT = "CREDIT"


class CustomerSegment(str, Enum):
    """Bank customer segment classification."""
    RETAIL = "RETAIL"
    PRIVATE = "PRIVATE"
    CORPORATE = "CORPORATE"
    SME = "SME"
    WEALTH = "WEALTH"
