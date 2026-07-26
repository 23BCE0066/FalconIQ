"""
Router: Dashboard

GET /api/v1/dashboard

Returns a complete, visualization-ready dashboard payload for compliance
officers. All chart data is pre-aggregated — the frontend renders charts
directly from the response without any further calculations.
"""
from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.api.common.response_envelope import RequestContext, get_request_context
from app.api.common.response_mapper import DashboardDTO
from app.core.dependencies import get_dashboard_service
from app.logging.logger import get_logger
from app.services.dashboard import DashboardService

router = APIRouter()
logger = get_logger(__name__)


@router.get(
    "/dashboard",
    summary="Platform dashboard",
    description=(
        "Returns a complete, visualization-ready dashboard payload including "
        "KPI summary metrics, risk distribution, country distribution, alert trends, "
        "top triggered AML rules, recent alerts, recent investigations, and an activity timeline. "
        "The frontend renders charts directly from this response — no additional calculations required."
    ),
    response_description="Dashboard payload with all charts and metrics pre-computed.",
    responses={
        200: {
            "description": "Dashboard data successfully retrieved.",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": {
                            "total_customers": 1200,
                            "total_transactions": 48300,
                            "total_alerts": 156,
                            "high_risk_customers": 43,
                            "average_risk_score": 38.4,
                            "risk_distribution": {"LOW": 800, "MEDIUM": 300, "HIGH": 80, "CRITICAL": 20},
                        },
                        "metadata": {
                            "request_id": "req_abc123",
                            "execution_time_ms": 95.3,
                            "timestamp": "2026-01-01T00:00:00+00:00",
                            "version": "v1",
                        },
                    }
                }
            },
        },
        500: {"description": "Internal server error."},
    },
    tags=["Dashboard"],
)
async def get_dashboard(
    ctx: Annotated[RequestContext, Depends(get_request_context)],
    dashboard_svc: Annotated[DashboardService, Depends(get_dashboard_service)],
) -> dict:
    """
    Returns all dashboard data in a single API call.

    Designed for the FalconIQ compliance dashboard page. Every metric and
    chart data point is pre-computed server-side.
    """
    logger.info("dashboard_request", request_id=ctx.request_id)

    dashboard = dashboard_svc.get_dashboard()

    logger.info(
        "dashboard_served",
        request_id=ctx.request_id,
        total_customers=dashboard.total_customers,
        total_alerts=dashboard.total_alerts,
    )

    return ctx.ok(dashboard.model_dump())
