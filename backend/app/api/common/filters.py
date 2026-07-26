"""
Common: Filters

Defines reusable filter dependency classes for list endpoints.
Inject via FastAPI Depends() — all query params are parsed automatically.

Rules:
    - Filter logic lives in Services/Repositories only.
    - These classes carry parsed, validated filter values to the service layer.
    - Never duplicate filter definitions across routers.

Usage:
    @router.get("/customers")
    async def list_customers(
        filters: Annotated[CustomerFilters, Depends()],
    ) -> dict:
        items, total = svc.list_customers(filters=filters, ...)
"""
from datetime import date
from typing import Optional

from fastapi import Query

from app.constants import AlertStatus, KYCStatus, RiskLevel, TransactionType


# ── Customer Filters ───────────────────────────────────────────────────────────

class CustomerFilters:
    """
    Query parameter filters for GET /api/v1/customers.

    All fields are Optional — unset fields are ignored in the service layer.
    """

    def __init__(
        self,
        search: Optional[str] = Query(
            default=None,
            description="Free-text search on name or email",
            max_length=255,
        ),
        risk_level: Optional[RiskLevel] = Query(
            default=None,
            description="Filter by risk classification",
        ),
        kyc_status: Optional[KYCStatus] = Query(
            default=None,
            description="Filter by KYC verification status",
        ),
        country: Optional[str] = Query(
            default=None,
            description="Filter by ISO 3166-1 alpha-3 country code",
            max_length=3,
        ),
        sort_by: str = Query(
            default="created_at",
            description="Field to sort by (created_at, name, risk_category, annual_income)",
        ),
        sort_desc: bool = Query(
            default=True,
            description="Sort descending if true",
        ),
    ) -> None:
        self.search = search
        self.risk_level = risk_level
        self.kyc_status = kyc_status
        self.country = country
        self.sort_by = sort_by
        self.sort_desc = sort_desc


# ── Transaction Filters ────────────────────────────────────────────────────────

class TransactionFilters:
    """
    Query parameter filters for GET /api/v1/transactions.
    """

    def __init__(
        self,
        customer_id: Optional[str] = Query(
            default=None,
            description="Filter by sender customer ID",
        ),
        country: Optional[str] = Query(
            default=None,
            description="ISO 3166-1 alpha-3 country code",
            max_length=3,
        ),
        tx_type: Optional[TransactionType] = Query(
            default=None,
            description="Transaction type filter",
        ),
        min_amount: Optional[float] = Query(
            default=None,
            ge=0,
            description="Minimum transaction amount (inclusive)",
        ),
        max_amount: Optional[float] = Query(
            default=None,
            ge=0,
            description="Maximum transaction amount (inclusive)",
        ),
        date_from: Optional[date] = Query(
            default=None,
            description="Start date filter (YYYY-MM-DD)",
        ),
        date_to: Optional[date] = Query(
            default=None,
            description="End date filter (YYYY-MM-DD)",
        ),
        is_cross_border: Optional[bool] = Query(
            default=None,
            description="Filter cross-border transactions only",
        ),
        is_weekend: Optional[bool] = Query(
            default=None,
            description="Filter weekend transactions only",
        ),
        risk_flagged: Optional[bool] = Query(
            default=None,
            description="Filter transactions that have associated alerts",
        ),
        sort_by: str = Query(
            default="timestamp",
            description="Field to sort by (timestamp, amount, country)",
        ),
        sort_desc: bool = Query(
            default=True,
            description="Sort descending if true",
        ),
    ) -> None:
        self.customer_id = customer_id
        self.country = country
        self.tx_type = tx_type
        self.min_amount = min_amount
        self.max_amount = max_amount
        self.date_from = date_from
        self.date_to = date_to
        self.is_cross_border = is_cross_border
        self.is_weekend = is_weekend
        self.risk_flagged = risk_flagged
        self.sort_by = sort_by
        self.sort_desc = sort_desc


# ── Alert Filters ──────────────────────────────────────────────────────────────

class AlertFilters:
    """
    Query parameter filters for GET /api/v1/alerts.
    """

    def __init__(
        self,
        customer_id: Optional[str] = Query(
            default=None,
            description="Filter by customer ID",
        ),
        status: Optional[AlertStatus] = Query(
            default=None,
            description="Filter by alert status",
        ),
        risk_level: Optional[RiskLevel] = Query(
            default=None,
            description="Filter by risk classification",
        ),
        rule_triggered: Optional[str] = Query(
            default=None,
            description="Filter by triggered rule name",
        ),
        date_from: Optional[date] = Query(
            default=None,
            description="Start date filter (YYYY-MM-DD)",
        ),
        date_to: Optional[date] = Query(
            default=None,
            description="End date filter (YYYY-MM-DD)",
        ),
        sort_by: str = Query(
            default="created_at",
            description="Field to sort by (created_at, risk_score, status)",
        ),
        sort_desc: bool = Query(
            default=True,
            description="Sort descending if true",
        ),
    ) -> None:
        self.customer_id = customer_id
        self.status = status
        self.risk_level = risk_level
        self.rule_triggered = rule_triggered
        self.date_from = date_from
        self.date_to = date_to
        self.sort_by = sort_by
        self.sort_desc = sort_desc
