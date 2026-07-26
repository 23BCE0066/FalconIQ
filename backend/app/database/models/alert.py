"""
SQLModel Domain Model: Alert

Represents a compliance alert raised by the rule engine, ML engine, or both.
Supports full HITL (Human-in-the-Loop) lifecycle: PENDING → APPROVED/DISMISSED.
"""
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel

from app.constants import AlertStatus, DetectionType, RiskLevel
from app.utils.id_generator import generate_alert_id
from app.utils.time import utcnow


class AlertBase(SQLModel):
    """Shared alert fields."""

    customer_id: str = Field(index=True, description="Customer who triggered this alert")
    transaction_id: Optional[str] = Field(default=None, index=True, description="Related transaction, if applicable")
    detection_type: DetectionType = Field(description="Whether detected by rule, ML, or both")
    rule_triggered: Optional[str] = Field(default=None, description="Name of the AML rule that triggered the alert")
    ml_model: Optional[str] = Field(default=None, description="ML model that flagged this entity")
    risk_score: float = Field(ge=0.0, le=100.0, description="Composite risk score (0–100)")
    risk_level: RiskLevel = Field(description="Risk classification derived from score")
    aml_pattern: Optional[str] = Field(default=None, description="AML pattern identified (e.g. STRUCTURING)")
    evidence: Optional[str] = Field(default=None, description="JSON-serialized evidence supporting the alert")
    session_id: Optional[str] = Field(default=None, description="Investigation session that generated this alert")


class Alert(AlertBase, table=True):
    """
    Persisted alert entity.

    Tracks the full lifecycle of a compliance alert including officer review,
    notes, and final disposition. Immutable audit-trail friendly.
    """

    __tablename__ = "alerts"

    alert_id: str = Field(
        default_factory=generate_alert_id,
        primary_key=True,
        description="Unique alert identifier (e.g. alert_abc123)"
    )
    status: AlertStatus = Field(default=AlertStatus.PENDING, description="Current review status")
    officer_notes: Optional[str] = Field(default=None, description="Compliance officer notes on review")
    reviewed_by: Optional[str] = Field(default=None, description="Officer who actioned this alert")
    reviewed_at: Optional[datetime] = Field(default=None, description="Timestamp of review")
    created_at: datetime = Field(default_factory=utcnow)


class AlertRead(AlertBase):
    """Read schema returned by the API."""
    alert_id: str
    status: AlertStatus
    officer_notes: Optional[str]
    reviewed_by: Optional[str]
    reviewed_at: Optional[datetime]
    created_at: datetime


class AlertCreate(AlertBase):
    """Write schema for creating an alert."""
    pass


class AlertActionRequest(SQLModel):
    """Request body for a HITL compliance officer action on an alert."""
    action: AlertStatus
    notes: Optional[str] = Field(default=None, description="Officer notes or rationale")
    reviewed_by: str = Field(description="Identifier of the officer taking action")
