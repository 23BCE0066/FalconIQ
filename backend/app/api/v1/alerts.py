"""
Router: Alerts

GET  /api/v1/alerts                      — paginated + filtered list
GET  /api/v1/alerts/{alert_id}           — single alert detail
POST /api/v1/alerts/{alert_id}/approve   — HITL approve action
POST /api/v1/alerts/{alert_id}/dismiss   — HITL dismiss action
POST /api/v1/alerts/{alert_id}/assign    — Assign to analyst
"""
from datetime import datetime, timezone
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Path, Query
from pydantic import BaseModel, Field
from sqlmodel import Session, and_, func, select

from app.api.common.filters import AlertFilters
from app.api.common.pagination import PageRequest
from app.api.common.response_envelope import RequestContext, get_request_context
from app.api.common.response_mapper import AlertActionResponseDTO, AlertDTO, ResponseMapper
from app.constants import AlertStatus
from app.core.dependencies import get_alert_service
from app.database.engine import get_session
from app.database.models.alert import Alert, AlertActionRequest
from app.logging.logger import get_logger
from app.services.alert import AlertService

router = APIRouter()
logger = get_logger(__name__)


# ── Request Bodies ─────────────────────────────────────────────────────────────

class AlertActionBody(BaseModel):
    """HITL action request body."""
    reviewed_by: str = Field(
        ..., min_length=1, description="Identifier of the compliance officer taking action"
    )
    notes: Optional[str] = Field(
        default=None, max_length=2000, description="Analyst notes or rationale"
    )


class AssignAlertBody(BaseModel):
    """Alert assignment request body."""
    assignee_id: str = Field(
        ..., min_length=1, description="Identifier of the analyst to assign this alert to"
    )
    notes: Optional[str] = Field(
        default=None, max_length=2000, description="Assignment notes"
    )


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.get(
    "/alerts",
    summary="List alerts",
    description=(
        "Returns a paginated list of compliance alerts. Supports filtering by "
        "customer ID, status, risk level, triggered rule, and date range."
    ),
    response_description="Paginated alert list.",
    tags=["Alerts"],
    responses={
        200: {"description": "Alert list retrieved successfully."},
        422: {"description": "Invalid filter or pagination parameter."},
    },
)
async def list_alerts(
    ctx: Annotated[RequestContext, Depends(get_request_context)],
    pagination: Annotated[PageRequest, Depends()],
    filters: Annotated[AlertFilters, Depends()],
    db: Annotated[Session, Depends(get_session)],
) -> dict:
    """
    Paginated alert list with comprehensive filter support.

    **Filters:**
    - `customer_id` — Filter by customer
    - `status` — PENDING | APPROVED | DISMISSED | UNDER_REVIEW | ESCALATED
    - `risk_level` — LOW | MEDIUM | HIGH | CRITICAL
    - `rule_triggered` — Rule name substring
    - `date_from` / `date_to` — Date range (YYYY-MM-DD)
    """
    from datetime import datetime, timezone

    conditions = []

    if filters.customer_id:
        conditions.append(Alert.customer_id == filters.customer_id)
    if filters.status:
        conditions.append(Alert.status == filters.status)
    if filters.risk_level:
        conditions.append(Alert.risk_level == filters.risk_level)
    if filters.rule_triggered:
        conditions.append(Alert.rule_triggered == filters.rule_triggered)
    if filters.date_from:
        dt_from = datetime(filters.date_from.year, filters.date_from.month, filters.date_from.day, tzinfo=timezone.utc)
        conditions.append(Alert.created_at >= dt_from)
    if filters.date_to:
        dt_to = datetime(filters.date_to.year, filters.date_to.month, filters.date_to.day, 23, 59, 59, tzinfo=timezone.utc)
        conditions.append(Alert.created_at <= dt_to)

    # Count
    count_stmt = select(func.count()).select_from(Alert)
    if conditions:
        count_stmt = count_stmt.where(and_(*conditions))
    total = db.exec(count_stmt).one() or 0

    # Data
    sort_map = {
        "created_at": Alert.created_at,
        "risk_score": Alert.risk_score,
        "status": Alert.status,
    }
    sort_col = sort_map.get(filters.sort_by, Alert.created_at)

    stmt = select(Alert)
    if conditions:
        stmt = stmt.where(and_(*conditions))
    if filters.sort_desc:
        stmt = stmt.order_by(sort_col.desc())  # type: ignore[attr-defined]
    else:
        stmt = stmt.order_by(sort_col.asc())  # type: ignore[attr-defined]
    stmt = stmt.offset(pagination.skip).limit(pagination.limit)

    alerts = list(db.exec(stmt).all())
    dtos = ResponseMapper.alerts(alerts)

    logger.info(
        "alerts_listed",
        request_id=ctx.request_id,
        total=total,
        page=pagination.page,
    )
    return ctx.ok(pagination.wrap(dtos, total).model_dump())


@router.get(
    "/alerts/{alert_id}",
    summary="Get alert detail",
    description="Returns the complete details of a single compliance alert by its ID.",
    response_description="Alert detail.",
    tags=["Alerts"],
    responses={
        200: {"description": "Alert retrieved successfully."},
        404: {"description": "Alert not found."},
    },
)
async def get_alert(
    ctx: Annotated[RequestContext, Depends(get_request_context)],
    alert_id: str = Path(..., description="Alert ID (e.g. alert_abc123)"),
    alert_svc: Annotated[AlertService, Depends(get_alert_service)] = None,
) -> dict:
    """Returns a single alert by ID."""
    alert = alert_svc.get_alert(alert_id)
    dto = ResponseMapper.alert(alert)

    logger.info("alert_retrieved", request_id=ctx.request_id, alert_id=alert_id)
    return ctx.ok(dto.model_dump())


@router.post(
    "/alerts/{alert_id}/approve",
    summary="Approve alert",
    description=(
        "Applies a HITL compliance officer APPROVED decision to a pending alert. "
        "Analyst notes are stored with the decision. Returns the updated alert status."
    ),
    response_description="Alert action result.",
    tags=["Alerts"],
    responses={
        200: {"description": "Alert approved successfully."},
        400: {"description": "Alert already actioned or invalid state."},
        404: {"description": "Alert not found."},
    },
)
async def approve_alert(
    ctx: Annotated[RequestContext, Depends(get_request_context)],
    body: AlertActionBody,
    alert_id: str = Path(..., description="Alert ID to approve"),
    alert_svc: Annotated[AlertService, Depends(get_alert_service)] = None,
) -> dict:
    """Approves a pending compliance alert."""
    action_req = AlertActionRequest(
        action=AlertStatus.APPROVED,
        notes=body.notes,
        reviewed_by=body.reviewed_by,
    )
    updated = alert_svc.apply_action(alert_id, action_req)
    result = AlertActionResponseDTO(
        alert_id=updated.alert_id,
        previous_status=AlertStatus.PENDING.value,
        new_status=str(updated.status.value if hasattr(updated.status, "value") else updated.status),
        reviewed_by=updated.reviewed_by or body.reviewed_by,
        reviewed_at=updated.reviewed_at or datetime.now(timezone.utc),
        notes=updated.officer_notes,
    )

    logger.info(
        "alert_approved",
        request_id=ctx.request_id,
        alert_id=alert_id,
        reviewed_by=body.reviewed_by,
    )
    return ctx.ok(result.model_dump())


@router.post(
    "/alerts/{alert_id}/dismiss",
    summary="Dismiss alert",
    description=(
        "Applies a HITL compliance officer DISMISSED decision to a pending alert. "
        "Analyst notes are stored with the dismissal. Returns the updated alert status."
    ),
    response_description="Alert action result.",
    tags=["Alerts"],
    responses={
        200: {"description": "Alert dismissed successfully."},
        400: {"description": "Alert already actioned or invalid state."},
        404: {"description": "Alert not found."},
    },
)
async def dismiss_alert(
    ctx: Annotated[RequestContext, Depends(get_request_context)],
    body: AlertActionBody,
    alert_id: str = Path(..., description="Alert ID to dismiss"),
    alert_svc: Annotated[AlertService, Depends(get_alert_service)] = None,
) -> dict:
    """Dismisses a pending compliance alert."""
    action_req = AlertActionRequest(
        action=AlertStatus.DISMISSED,
        notes=body.notes,
        reviewed_by=body.reviewed_by,
    )
    updated = alert_svc.apply_action(alert_id, action_req)
    result = AlertActionResponseDTO(
        alert_id=updated.alert_id,
        previous_status=AlertStatus.PENDING.value,
        new_status=str(updated.status.value if hasattr(updated.status, "value") else updated.status),
        reviewed_by=updated.reviewed_by or body.reviewed_by,
        reviewed_at=updated.reviewed_at or datetime.now(timezone.utc),
        notes=updated.officer_notes,
    )

    logger.info(
        "alert_dismissed",
        request_id=ctx.request_id,
        alert_id=alert_id,
        reviewed_by=body.reviewed_by,
    )
    return ctx.ok(result.model_dump())


@router.post(
    "/alerts/{alert_id}/pending",
    summary="Set alert to Pending",
    description=(
        "Resets or transitions an alert status back to PENDING. "
        "Analyst notes are stored with the action. Returns the updated alert status."
    ),
    response_description="Alert action result.",
    tags=["Alerts"],
    responses={
        200: {"description": "Alert status set to PENDING successfully."},
        400: {"description": "Invalid state."},
        404: {"description": "Alert not found."},
    },
)
async def pending_alert(
    ctx: Annotated[RequestContext, Depends(get_request_context)],
    body: AlertActionBody,
    alert_id: str = Path(..., description="Alert ID to set to pending"),
    alert_svc: Annotated[AlertService, Depends(get_alert_service)] = None,
) -> dict:
    """Sets an alert's lifecycle status back to PENDING."""
    action_req = AlertActionRequest(
        action=AlertStatus.PENDING,
        notes=body.notes,
        reviewed_by=body.reviewed_by,
    )
    updated = alert_svc.apply_action(alert_id, action_req)
    result = AlertActionResponseDTO(
        alert_id=updated.alert_id,
        previous_status=str(updated.status.value if hasattr(updated.status, "value") else updated.status),
        new_status=AlertStatus.PENDING.value,
        reviewed_by=updated.reviewed_by or body.reviewed_by,
        reviewed_at=updated.reviewed_at or datetime.now(timezone.utc),
        notes=updated.officer_notes,
    )

    logger.info(
        "alert_set_to_pending",
        request_id=ctx.request_id,
        alert_id=alert_id,
        reviewed_by=body.reviewed_by,
    )
    return ctx.ok(result.model_dump())


@router.post(
    "/alerts/{alert_id}/assign",
    summary="Assign alert to analyst",
    description=(
        "Assigns an alert to a specific compliance analyst for review. "
        "Status changes to UNDER_REVIEW. Analyst notes are accepted."
    ),
    response_description="Alert assignment result.",
    tags=["Alerts"],
    responses={
        200: {"description": "Alert assigned successfully."},
        400: {"description": "Alert already actioned or invalid state."},
        404: {"description": "Alert not found."},
    },
)
async def assign_alert(
    ctx: Annotated[RequestContext, Depends(get_request_context)],
    body: AssignAlertBody,
    alert_id: str = Path(..., description="Alert ID to assign"),
    alert_svc: Annotated[AlertService, Depends(get_alert_service)] = None,
) -> dict:
    """Assigns a pending alert to an analyst — sets status to UNDER_REVIEW."""
    action_req = AlertActionRequest(
        action=AlertStatus.UNDER_REVIEW,
        notes=body.notes,
        reviewed_by=body.assignee_id,
    )
    updated = alert_svc.apply_action(alert_id, action_req)
    result = AlertActionResponseDTO(
        alert_id=updated.alert_id,
        previous_status=AlertStatus.PENDING.value,
        new_status=str(updated.status.value if hasattr(updated.status, "value") else updated.status),
        reviewed_by=updated.reviewed_by or body.assignee_id,
        reviewed_at=updated.reviewed_at or datetime.now(timezone.utc),
        notes=updated.officer_notes,
    )

    logger.info(
        "alert_assigned",
        request_id=ctx.request_id,
        alert_id=alert_id,
        assignee=body.assignee_id,
    )
    return ctx.ok(result.model_dump())
