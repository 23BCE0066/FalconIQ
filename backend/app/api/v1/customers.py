"""
Router: Customers

GET /api/v1/customers               — paginated, filtered, sortable list
GET /api/v1/customers/{customer_id} — full profile with risk, transactions, alerts
GET /api/v1/customers/{customer_id}/risk     — risk breakdown
GET /api/v1/customers/{customer_id}/timeline — event timeline
"""
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, Path, Query, Request, status
from fastapi.responses import JSONResponse
from sqlmodel import Session, and_, or_, select

from app.api.common.filters import CustomerFilters
from app.api.common.pagination import PageRequest, PageResponse
from app.api.common.response_envelope import RequestContext, get_request_context
from app.api.common.response_mapper import (
    AlertDTO,
    CustomerDTO,
    CustomerProfileDTO,
    CustomerRiskDTO,
    CustomerTimelineEventDTO,
    InvestigationSummaryDTO,
    ResponseMapper,
    TransactionDTO,
)
from app.constants import AlertStatus, RiskLevel
from app.core.dependencies import (
    get_alert_service,
    get_customer_service,
    get_statistics_service,
    get_transaction_service,
)
from app.core.exceptions import ValidationException
from app.database.engine import get_session
from app.database.models.alert import Alert
from app.database.models.customer import Customer
from app.database.models.session import AgentSession
from app.database.models.transaction import Transaction
from app.logging.logger import get_logger
from app.services.alert import AlertService
from app.services.customer import CustomerService
from app.services.statistics import StatisticsService
from app.services.transaction import TransactionService

router = APIRouter()
logger = get_logger(__name__)


@router.get(
    "/customers",
    summary="List customers",
    description=(
        "Returns a paginated, filtered list of all bank customers. "
        "Supports free-text search on name/email, risk level filter, KYC status filter, "
        "country filter, and sorting by any customer field."
    ),
    response_description="Paginated list of customers.",
    tags=["Customers"],
    responses={
        200: {"description": "Customer list retrieved successfully."},
        422: {"description": "Invalid filter or pagination parameter."},
    },
)
async def list_customers(
    ctx: Annotated[RequestContext, Depends(get_request_context)],
    pagination: Annotated[PageRequest, Depends()],
    filters: Annotated[CustomerFilters, Depends()],
    db: Annotated[Session, Depends(get_session)],
) -> dict:
    """
    Paginated customer list with search, sort, and filter support.

    **Filters:**
    - `search` — matches name or email (case-insensitive prefix)
    - `risk_level` — LOW, MEDIUM, HIGH, CRITICAL
    - `kyc_status` — PENDING, VERIFIED, FAILED, EXPIRED
    - `country` — ISO 3166-1 alpha-3 code (e.g. USA, GBR)
    - `sort_by` — created_at | name | risk_category | annual_income
    - `sort_desc` — boolean (default true)
    """
    # Build filter conditions
    conditions = []

    if filters.search:
        q = f"{filters.search}%"
        conditions.append(
            or_(
                Customer.name.startswith(filters.search),   # type: ignore[attr-defined]
                Customer.email.startswith(filters.search),  # type: ignore[attr-defined]
            )
        )

    if filters.risk_level:
        conditions.append(Customer.risk_category == filters.risk_level)

    if filters.kyc_status:
        conditions.append(Customer.kyc_status == filters.kyc_status)

    if filters.country:
        conditions.append(Customer.country == filters.country)

    # Count
    from sqlmodel import func
    count_stmt = select(func.count()).select_from(Customer)
    if conditions:
        count_stmt = count_stmt.where(and_(*conditions))
    total = db.exec(count_stmt).one() or 0

    # Data
    sort_map = {
        "created_at": Customer.created_at,
        "name": Customer.name,
        "risk_category": Customer.risk_category,
        "annual_income": Customer.annual_income,
        "updated_at": Customer.updated_at,
    }
    sort_col = sort_map.get(filters.sort_by, Customer.created_at)

    stmt = select(Customer)
    if conditions:
        stmt = stmt.where(and_(*conditions))
    if filters.sort_desc:
        stmt = stmt.order_by(sort_col.desc())  # type: ignore[attr-defined]
    else:
        stmt = stmt.order_by(sort_col.asc())   # type: ignore[attr-defined]
    stmt = stmt.offset(pagination.skip).limit(pagination.limit)

    customers = list(db.exec(stmt).all())
    dtos = ResponseMapper.customers(customers)

    logger.info(
        "customers_listed",
        request_id=ctx.request_id,
        total=total,
        page=pagination.page,
    )
    return ctx.ok(pagination.wrap(dtos, total).model_dump())


@router.get(
    "/customers/{customer_id}",
    summary="Get customer profile",
    description=(
        "Returns the full customer profile including risk summary, recent transactions, "
        "triggered alerts, and investigation history."
    ),
    response_description="Full customer profile.",
    tags=["Customers"],
    responses={
        200: {"description": "Customer profile retrieved successfully."},
        404: {"description": "Customer not found."},
    },
)
async def get_customer_profile(
    ctx: Annotated[RequestContext, Depends(get_request_context)],
    customer_id: str = Path(..., description="Customer ID (e.g. cust_abc123)"),
    db: Annotated[Session, Depends(get_session)] = None,
    customer_svc: Annotated[CustomerService, Depends(get_customer_service)] = None,
    transaction_svc: Annotated[TransactionService, Depends(get_transaction_service)] = None,
    alert_svc: Annotated[AlertService, Depends(get_alert_service)] = None,
    stats_svc: Annotated[StatisticsService, Depends(get_statistics_service)] = None,
) -> dict:
    """Full customer profile with associated risk, transactions, alerts, and investigations."""
    # Customer
    customer = customer_svc.get_customer(customer_id)
    customer_dto = ResponseMapper.customer(customer)

    # Recent transactions (sent or received)
    recent_txns = transaction_svc.get_customer_transactions(customer_id, limit=10)
    txn_dtos = ResponseMapper.transactions(recent_txns)

    # Alerts
    alerts_orm = alert_svc.get_customer_alerts(customer_id)
    alert_dtos = ResponseMapper.alerts(alerts_orm)

    # Risk summary
    pending_alerts = sum(1 for a in alerts_orm if str(a.status.value if hasattr(a.status, "value") else a.status) == AlertStatus.PENDING.value)
    risk_summary = CustomerRiskDTO(
        customer_id=customer_id,
        name=customer.name,
        risk_category=str(customer.risk_category.value if hasattr(customer.risk_category, "value") else customer.risk_category),
        kyc_status=str(customer.kyc_status.value if hasattr(customer.kyc_status, "value") else customer.kyc_status),
        alert_count=len(alerts_orm),
        pending_alerts=pending_alerts,
        high_value_transactions=sum(1 for t in recent_txns if t.amount > 10000),
        recommendation=_risk_recommendation(customer.risk_category),
    )

    # Investigation history
    inv_stmt = (
        select(AgentSession)
        .order_by(AgentSession.created_at.desc())  # type: ignore[attr-defined]
        .limit(5)
    )
    sessions_orm = list(db.exec(inv_stmt).all())
    inv_history = [ResponseMapper.investigation_summary(s) for s in sessions_orm]

    profile = CustomerProfileDTO(
        customer=customer_dto,
        risk_summary=risk_summary,
        recent_transactions=txn_dtos,
        triggered_alerts=alert_dtos,
        investigation_history=inv_history,
    )

    logger.info(
        "customer_profile_served",
        request_id=ctx.request_id,
        customer_id=customer_id,
    )
    return ctx.ok(profile.model_dump())


@router.get(
    "/customers/{customer_id}/risk",
    summary="Get customer risk breakdown",
    description=(
        "Returns a detailed risk breakdown for a specific customer, including "
        "their current risk level, alert history, and compliance recommendation."
    ),
    response_description="Customer risk summary.",
    tags=["Customers"],
    responses={
        200: {"description": "Risk breakdown retrieved successfully."},
        404: {"description": "Customer not found."},
    },
)
async def get_customer_risk(
    ctx: Annotated[RequestContext, Depends(get_request_context)],
    customer_id: str = Path(..., description="Customer ID"),
    customer_svc: Annotated[CustomerService, Depends(get_customer_service)] = None,
    alert_svc: Annotated[AlertService, Depends(get_alert_service)] = None,
    transaction_svc: Annotated[TransactionService, Depends(get_transaction_service)] = None,
) -> dict:
    """Risk breakdown for a specific customer."""
    customer = customer_svc.get_customer(customer_id)
    alerts_orm = alert_svc.get_customer_alerts(customer_id)
    recent_txns = transaction_svc.get_customer_transactions(customer_id, limit=100)

    pending = sum(1 for a in alerts_orm if str(a.status.value if hasattr(a.status, "value") else a.status) == AlertStatus.PENDING.value)
    avg_risk = sum(a.risk_score for a in alerts_orm) / len(alerts_orm) if alerts_orm else 0.0
    high_value = sum(1 for t in recent_txns if t.amount > 10000)

    risk_data = CustomerRiskDTO(
        customer_id=customer_id,
        name=customer.name,
        risk_category=str(customer.risk_category.value if hasattr(customer.risk_category, "value") else customer.risk_category),
        kyc_status=str(customer.kyc_status.value if hasattr(customer.kyc_status, "value") else customer.kyc_status),
        risk_score=round(avg_risk, 2),
        alert_count=len(alerts_orm),
        pending_alerts=pending,
        high_value_transactions=high_value,
        recommendation=_risk_recommendation(customer.risk_category),
    )

    logger.info("customer_risk_served", request_id=ctx.request_id, customer_id=customer_id)
    return ctx.ok(risk_data.model_dump())


@router.get(
    "/customers/{customer_id}/timeline",
    summary="Get customer event timeline",
    description=(
        "Returns a chronological event timeline for a customer including transactions, "
        "alerts, and investigation events. Useful for compliance audit views."
    ),
    response_description="Chronological customer event timeline.",
    tags=["Customers"],
    responses={
        200: {"description": "Timeline retrieved successfully."},
        404: {"description": "Customer not found."},
    },
)
async def get_customer_timeline(
    ctx: Annotated[RequestContext, Depends(get_request_context)],
    customer_id: str = Path(..., description="Customer ID"),
    limit: int = Query(default=50, ge=1, le=200, description="Max events to return"),
    customer_svc: Annotated[CustomerService, Depends(get_customer_service)] = None,
    alert_svc: Annotated[AlertService, Depends(get_alert_service)] = None,
    transaction_svc: Annotated[TransactionService, Depends(get_transaction_service)] = None,
) -> dict:
    """Chronological event timeline for a customer."""
    # Validate customer exists
    customer_svc.get_customer(customer_id)

    events: List[CustomerTimelineEventDTO] = []

    # Transaction events
    txns = transaction_svc.get_customer_transactions(customer_id, limit=limit)
    for t in txns:
        events.append(
            CustomerTimelineEventDTO(
                event_type="transaction",
                event_id=t.transaction_id,
                timestamp=t.timestamp,
                description=f"{t.type} of {t.currency} {t.amount:,.2f} to {t.receiver_id}",
                severity="high" if t.amount > 50000 else ("medium" if t.amount > 10000 else "low"),
                metadata={
                    "amount": t.amount,
                    "currency": t.currency,
                    "country": t.country,
                    "is_cross_border": t.is_cross_border,
                },
            )
        )

    # Alert events
    alert_list = alert_svc.get_customer_alerts(customer_id)
    for a in alert_list:
        rl = str(a.risk_level.value if hasattr(a.risk_level, "value") else a.risk_level)
        events.append(
            CustomerTimelineEventDTO(
                event_type="alert",
                event_id=a.alert_id,
                timestamp=a.created_at,
                description=f"Alert raised: {a.rule_triggered or a.aml_pattern or 'suspicious activity'}",
                severity=rl.lower(),
                metadata={
                    "risk_score": a.risk_score,
                    "status": str(a.status.value if hasattr(a.status, "value") else a.status),
                },
            )
        )

    # Sort chronologically (newest first)
    events.sort(key=lambda e: e.timestamp, reverse=True)
    events = events[:limit]

    logger.info(
        "customer_timeline_served",
        request_id=ctx.request_id,
        customer_id=customer_id,
        event_count=len(events),
    )
    return ctx.ok({"customer_id": customer_id, "events": [e.model_dump() for e in events]})


# ── Helper ─────────────────────────────────────────────────────────────────────

def _risk_recommendation(risk_category) -> str:
    """Returns a compliance recommendation string based on risk level."""
    rl = str(risk_category.value if hasattr(risk_category, "value") else risk_category)
    recommendations = {
        "CRITICAL": "Immediate account freeze and SAR filing recommended.",
        "HIGH": "Manual review required by L2 compliance officer.",
        "MEDIUM": "Monitor account activity and re-evaluate in 30 days.",
        "LOW": "No immediate action required. Continue standard monitoring.",
    }
    return recommendations.get(rl, "No immediate action required.")
