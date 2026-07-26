"""
Common: ResponseMapper

Defines all public API DTO classes and static factory methods that convert
SQLModel ORM objects into serialisation-safe Pydantic models.

Rules enforced here:
    - No SQLModel table object ever leaves this module exposed to a router.
    - No ExecutionContext, ToolResult, or internal schema leaks.
    - All DTO fields are primitive types or nested DTOs.

Usage:
    customer_dto = ResponseMapper.customer(customer_orm)
    alert_dto    = ResponseMapper.alert(alert_orm)
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── Customer DTOs ──────────────────────────────────────────────────────────────

class CustomerDTO(BaseModel):
    """Public customer representation — no SQLModel internals."""
    customer_id: str
    name: str
    email: str
    occupation: Optional[str] = None
    annual_income: float
    risk_category: str
    kyc_status: str
    customer_segment: str
    country: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CustomerRiskDTO(BaseModel):
    """Risk summary for a specific customer."""
    customer_id: str
    name: str
    risk_category: str
    kyc_status: str
    risk_score: Optional[float] = None
    alert_count: int = 0
    pending_alerts: int = 0
    high_value_transactions: int = 0
    recommendation: str = "No immediate action required."


class CustomerTimelineEventDTO(BaseModel):
    """A single timeline event for a customer."""
    event_type: str  # "transaction", "alert", "investigation", "kyc"
    event_id: str
    timestamp: datetime
    description: str
    severity: str = "low"  # low, medium, high, critical
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CustomerProfileDTO(BaseModel):
    """Full customer profile with associated data."""
    customer: CustomerDTO
    risk_summary: CustomerRiskDTO
    recent_transactions: List["TransactionDTO"] = Field(default_factory=list)
    triggered_alerts: List["AlertDTO"] = Field(default_factory=list)
    investigation_history: List["InvestigationSummaryDTO"] = Field(default_factory=list)


# ── Transaction DTOs ───────────────────────────────────────────────────────────

class TransactionDTO(BaseModel):
    """Public transaction representation."""
    transaction_id: str
    sender_id: str
    receiver_id: str
    type: str
    amount: float
    currency: str
    country: str
    timestamp: datetime
    is_cross_border: bool
    is_weekend: bool
    is_night: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Alert DTOs ─────────────────────────────────────────────────────────────────

class AlertDTO(BaseModel):
    """Public alert representation."""
    alert_id: str
    customer_id: str
    transaction_id: Optional[str] = None
    detection_type: str
    rule_triggered: Optional[str] = None
    ml_model: Optional[str] = None
    risk_score: float
    risk_level: str
    aml_pattern: Optional[str] = None
    evidence: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None
    status: str
    officer_notes: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AlertActionResponseDTO(BaseModel):
    """Response for a HITL action on an alert."""
    alert_id: str
    previous_status: str
    new_status: str
    reviewed_by: str
    reviewed_at: datetime
    notes: Optional[str] = None


# ── Investigation DTOs ─────────────────────────────────────────────────────────

class InvestigationSummaryDTO(BaseModel):
    """Summary of a single agent investigation session."""
    session_id: str
    query: str
    status: str
    intent: Optional[str] = None
    total_execution_time_ms: Optional[float] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    tool_count: Optional[int] = 0


class InvestigationDetailDTO(BaseModel):
    """Detailed investigation result with timeline."""
    session_id: str
    query: str
    status: str
    intent: Optional[str] = None
    execution_plan: List[str] = Field(default_factory=list)
    total_execution_time_ms: Optional[float] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    tool_steps: List["ToolStepDTO"] = Field(default_factory=list)


class ToolStepDTO(BaseModel):
    """A single tool execution step in the investigation timeline."""
    log_id: str
    tool_name: str
    step_order: int
    success: bool
    execution_time_ms: float
    confidence: Optional[float] = None
    summary: Optional[str] = None
    explanation: Optional[str] = None
    created_at: datetime


# ── Dashboard DTOs ─────────────────────────────────────────────────────────────

class RiskDistributionDTO(BaseModel):
    """Risk distribution chart data."""
    LOW: int = 0
    MEDIUM: int = 0
    HIGH: int = 0
    CRITICAL: int = 0


class AlertStatisticsDTO(BaseModel):
    """Alert count aggregated by status."""
    total: int = 0
    pending: int = 0
    approved: int = 0
    dismissed: int = 0
    under_review: int = 0
    escalated: int = 0


class TrendDataPointDTO(BaseModel):
    """Single data point for trend chart."""
    period: str  # ISO date string or "YYYY-MM"
    value: float
    label: Optional[str] = None


class CountryDistributionDTO(BaseModel):
    """Per-country transaction/alert data."""
    country: str
    transaction_count: int = 0
    alert_count: int = 0
    total_volume: float = 0.0


class TopRuleDTO(BaseModel):
    """A triggered AML rule and its trigger count."""
    rule_name: str
    trigger_count: int
    percentage: float = 0.0
    type: str = "Rule"
    accuracy: float = 90.0
    status: str = "Active"
    last_trained_at: Optional[datetime] = None


class RecentActivityDTO(BaseModel):
    """A single recent AML activity item."""
    event_id: str
    event_type: str  # "alert", "investigation", "transaction"
    timestamp: datetime
    description: str
    severity: str
    customer_id: Optional[str] = None


class DashboardDTO(BaseModel):
    """Complete dashboard payload — frontend renders charts directly."""
    # Summary metrics
    total_customers: int
    total_transactions: int
    total_alerts: int
    total_cases_under_review: int = 86
    total_sar_filed: int = 22
    high_risk_customers: int
    average_risk_score: float

    # Percentage changes compared to previous period
    pct_change_customers: float = 0.0
    pct_change_transactions: float = 0.0
    pct_change_alerts: float = 0.0
    pct_change_cases_under_review: float = 0.0
    pct_change_sar_filed: float = 0.0
    pct_change_high_risk: float = 0.0

    # Chart-ready data
    risk_distribution: RiskDistributionDTO
    country_distribution: List[CountryDistributionDTO] = Field(default_factory=list)
    alert_trends: List[TrendDataPointDTO] = Field(default_factory=list)
    top_triggered_rules: List[TopRuleDTO] = Field(default_factory=list)
    top_suspicious_patterns: List[Dict[str, Any]] = Field(default_factory=list)

    # Recent items
    top_high_risk_alerts: List[AlertDTO] = Field(default_factory=list)
    recent_alerts: List[AlertDTO] = Field(default_factory=list)
    recent_investigations: List[InvestigationSummaryDTO] = Field(default_factory=list)
    activity_timeline: List[RecentActivityDTO] = Field(default_factory=list)


# ── Analytics DTOs ─────────────────────────────────────────────────────────────

class RiskAnalyticsDTO(BaseModel):
    """Risk analytics overview."""
    distribution: RiskDistributionDTO
    average_score: float
    high_risk_percentage: float
    critical_count: int
    kyc_breakdown: Dict[str, int] = Field(default_factory=dict)


class TrendsAnalyticsDTO(BaseModel):
    """Transaction and alert trends over time."""
    transaction_trends: List[TrendDataPointDTO] = Field(default_factory=list)
    alert_trends: List[TrendDataPointDTO] = Field(default_factory=list)
    volume_trends: List[TrendDataPointDTO] = Field(default_factory=list)


class RulesAnalyticsDTO(BaseModel):
    """AML rule analytics."""
    top_rules: List[TopRuleDTO] = Field(default_factory=list)
    total_triggered: int = 0
    rules_by_severity: Dict[str, int] = Field(default_factory=dict)


class CountriesAnalyticsDTO(BaseModel):
    """Country-level analytics."""
    countries: List[CountryDistributionDTO] = Field(default_factory=list)
    high_risk_countries: List[str] = Field(default_factory=list)
    cross_border_percentage: float = 0.0


class CustomerAnalyticsDTO(BaseModel):
    """Customer segment and risk breakdown."""
    total_customers: int
    by_segment: Dict[str, int] = Field(default_factory=dict)
    by_kyc_status: Dict[str, int] = Field(default_factory=dict)
    high_risk_customers: List[CustomerDTO] = Field(default_factory=list)


class ModelInfoDTO(BaseModel):
    name: str
    accuracy: float
    status: str
    type: str


class ModelsAnalyticsDTO(BaseModel):
    models: List[ModelInfoDTO]


class DatasetInfoDTO(BaseModel):
    name: str
    records: int
    size_bytes: int
    updated_at: str
    type: str
    status: str
    color: str


class DatasetsAnalyticsDTO(BaseModel):
    datasets: List[DatasetInfoDTO]
    uploaded_customer_records: int = 0
    uploaded_transaction_records: int = 0


# ── Network DTOs ───────────────────────────────────────────────────────────────

class NetworkNodeDTO(BaseModel):
    """A node in the transaction network graph."""
    id: str
    label: str
    type: str = "customer"  # customer, external
    risk_level: Optional[str] = None
    transaction_count: int = 0
    total_volume: float = 0.0


class NetworkEdgeDTO(BaseModel):
    """A directed edge in the transaction network graph."""
    source: str
    target: str
    weight: float  # total amount
    count: int     # number of transactions


class NetworkGraphDTO(BaseModel):
    """Graph-ready network analysis payload."""
    nodes: List[NetworkNodeDTO] = Field(default_factory=list)
    edges: List[NetworkEdgeDTO] = Field(default_factory=list)
    circular_patterns: List[List[str]] = Field(default_factory=list)
    layering_chains: List[List[str]] = Field(default_factory=list)
    hubs: List[Dict[str, Any]] = Field(default_factory=list)
    total_nodes: int = 0
    total_edges: int = 0
    suspicious_patterns_count: int = 0


class SuspiciousNetworkDTO(BaseModel):
    """Global suspicious network detection result."""
    graph: NetworkGraphDTO
    risk_clusters: List[List[str]] = Field(default_factory=list)
    most_connected_entities: List[NetworkNodeDTO] = Field(default_factory=list)


# ── Report DTOs ────────────────────────────────────────────────────────────────

class ReportDTO(BaseModel):
    """Generated report metadata and content."""
    report_id: str
    report_type: str  # "risk_summary", "transaction_analysis", "alert_report", "compliance"
    format: str       # "json", "markdown", "pdf"
    title: str
    generated_at: datetime
    status: str = "completed"
    content: Optional[Any] = None   # JSON content
    markdown: Optional[str] = None  # Markdown content
    summary: str = ""


# ── System DTOs ────────────────────────────────────────────────────────────────

class SubsystemStatusDTO(BaseModel):
    """Status of a single subsystem."""
    status: str  # "ok", "degraded", "error", "configured", "not_configured"
    details: Optional[str] = None
    error: Optional[str] = None


class SystemInfoDTO(BaseModel):
    """Complete system information payload."""
    application: str
    version: str
    build_number: str
    environment: str
    uptime_seconds: float
    uptime_human: str
    database: Dict[str, Any] = Field(default_factory=dict)
    gemini: Dict[str, Any] = Field(default_factory=dict)
    tool_registry: Dict[str, Any] = Field(default_factory=dict)
    ml_service: Dict[str, Any] = Field(default_factory=dict)
    loaded_models: List[str] = Field(default_factory=list)
    loaded_rules: List[str] = Field(default_factory=list)


# ── Mapper ─────────────────────────────────────────────────────────────────────

class ResponseMapper:
    """
    Static factory class that maps ORM objects to DTOs.
    Import and call: ResponseMapper.customer(orm_obj)
    """

    @staticmethod
    def customer(c: Any) -> CustomerDTO:
        """Maps a Customer ORM object to CustomerDTO."""
        return CustomerDTO(
            customer_id=c.customer_id,
            name=c.name,
            email=c.email,
            occupation=c.occupation,
            annual_income=c.annual_income,
            risk_category=str(c.risk_category.value if hasattr(c.risk_category, "value") else c.risk_category),
            kyc_status=str(c.kyc_status.value if hasattr(c.kyc_status, "value") else c.kyc_status),
            customer_segment=str(c.customer_segment.value if hasattr(c.customer_segment, "value") else c.customer_segment),
            country=c.country,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )

    @staticmethod
    def transaction(t: Any) -> TransactionDTO:
        """Maps a Transaction ORM object to TransactionDTO."""
        return TransactionDTO(
            transaction_id=t.transaction_id,
            sender_id=t.sender_id,
            receiver_id=t.receiver_id,
            type=str(t.type.value if hasattr(t.type, "value") else t.type),
            amount=t.amount,
            currency=t.currency,
            country=t.country,
            timestamp=t.timestamp,
            is_cross_border=t.is_cross_border,
            is_weekend=t.is_weekend,
            is_night=t.is_night,
            created_at=t.created_at,
        )

    @staticmethod
    def alert(a: Any) -> AlertDTO:
        """Maps an Alert ORM object to AlertDTO."""
        # Parse evidence JSON string if stored as string
        evidence = None
        if a.evidence:
            try:
                evidence = json.loads(a.evidence) if isinstance(a.evidence, str) else a.evidence
            except (json.JSONDecodeError, TypeError):
                evidence = {"raw": str(a.evidence)}

        return AlertDTO(
            alert_id=a.alert_id,
            customer_id=a.customer_id,
            transaction_id=a.transaction_id,
            detection_type=str(a.detection_type.value if hasattr(a.detection_type, "value") else a.detection_type),
            rule_triggered=a.rule_triggered,
            ml_model=a.ml_model,
            risk_score=a.risk_score,
            risk_level=str(a.risk_level.value if hasattr(a.risk_level, "value") else a.risk_level),
            aml_pattern=a.aml_pattern,
            evidence=evidence,
            session_id=a.session_id,
            status=str(a.status.value if hasattr(a.status, "value") else a.status),
            officer_notes=a.officer_notes,
            reviewed_by=a.reviewed_by,
            reviewed_at=a.reviewed_at,
            created_at=a.created_at,
        )

    @staticmethod
    def investigation_summary(session: Any) -> InvestigationSummaryDTO:
        """Maps an AgentSession ORM object to InvestigationSummaryDTO."""
        tool_count = 0
        if getattr(session, "execution_plan", None):
            try:
                plan = json.loads(session.execution_plan)
                if isinstance(plan, list):
                    tool_count = len(plan)
            except Exception:
                pass
        return InvestigationSummaryDTO(
            session_id=session.session_id,
            query=session.query,
            status=str(session.status.value if hasattr(session.status, "value") else session.status),
            intent=session.intent,
            total_execution_time_ms=session.total_execution_time_ms,
            created_at=session.created_at,
            completed_at=session.completed_at,
            tool_count=tool_count,
        )

    @staticmethod
    def tool_step(log: Any) -> ToolStepDTO:
        """Maps an AgentExecutionLog ORM object to ToolStepDTO."""
        return ToolStepDTO(
            log_id=log.log_id,
            tool_name=log.tool_name,
            step_order=log.step_order,
            success=log.success,
            execution_time_ms=log.execution_time_ms,
            confidence=log.confidence,
            summary=log.summary,
            explanation=log.explanation,
            created_at=log.created_at,
        )

    @staticmethod
    def customers(customers: list) -> List[CustomerDTO]:
        """Maps a list of Customer ORM objects."""
        return [ResponseMapper.customer(c) for c in customers]

    @staticmethod
    def transactions(transactions: list) -> List[TransactionDTO]:
        """Maps a list of Transaction ORM objects."""
        return [ResponseMapper.transaction(t) for t in transactions]

    @staticmethod
    def alerts(alerts: list) -> List[AlertDTO]:
        """Maps a list of Alert ORM objects."""
        return [ResponseMapper.alert(a) for a in alerts]
