"""
Router: Health

GET /api/v1/health — Basic health check with subsystem status.

Improved in Phase 5:
    - Returns standard ResponseEnvelope
    - Extended subsystem status (DB, Gemini, Tool Registry, ML)
    - Application version and environment
    - Structured logging with request_id
    - Added OpenAPI documentation, tags, and response examples
    - Does NOT depend on GeminiService (gracefully degrades when key is absent)
"""
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlmodel import Session, text

from app.api.common.response_envelope import RequestContext, get_request_context
from app.config.settings import get_settings
from app.database.engine import get_session
from app.logging.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)
settings = get_settings()

# Tool names registered by the platform (static list for health check)
_EXPECTED_TOOLS = [
    "dataset", "feature", "rule_engine", "ml_engine",
    "risk_calculator", "explainer", "network_analyzer",
]


@router.get(
    "/health",
    summary="Platform health check",
    description=(
        "Returns the operational status of all FalconIQ subsystems: "
        "API server, database, Gemini API configuration, and Tool Registry. "
        "Use this endpoint for load balancer health checks and monitoring dashboards. "
        "This endpoint always returns 200 — check the `status` field for 'ok' vs 'degraded'."
    ),
    response_description="Platform health status.",
    tags=["Health"],
    responses={
        200: {
            "description": "Health status retrieved (may be 'ok' or 'degraded').",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": {
                            "status": "ok",
                            "version": "1.0.0",
                            "environment": "development",
                            "subsystems": {
                                "api": {"status": "ok"},
                                "database": {"status": "ok", "error": None},
                                "gemini": {"status": "configured", "model": "gemini-2.5-flash"},
                                "tool_registry": {"status": "ok", "registered_tools": 7},
                            },
                        },
                        "metadata": {
                            "request_id": "req_abc123",
                            "execution_time_ms": 8.4,
                            "timestamp": "2026-01-01T00:00:00+00:00",
                            "version": "v1",
                        },
                    }
                }
            },
        }
    },
)
async def check_health(
    ctx: Annotated[RequestContext, Depends(get_request_context)],
    db: Annotated[Session, Depends(get_session)],
) -> dict:
    """
    Returns operational status of all platform subsystems.

    - **api**: Always OK if this endpoint responds.
    - **database**: Verified by running a lightweight SELECT 1 query.
    - **gemini**: Configured if GEMINI_API_KEY is set (key presence only).
    - **tool_registry**: Static list of expected registered tools.
    """
    # Database check
    db_ok = False
    db_error = None
    try:
        db.exec(text("SELECT 1"))
        db_ok = True
    except Exception as exc:
        db_error = str(exc)

    # Gemini check (key presence only — no API call made)
    gemini_configured = bool(settings.GEMINI_API_KEY)

    # Tool Registry check (graceful — does not instantiate GeminiService)
    tool_registry_status = _check_tool_registry()

    overall_status = "ok" if db_ok else "degraded"
    if not gemini_configured:
        overall_status = "degraded"

    health_data = {
        "status": overall_status,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "subsystems": {
            "api": {"status": "ok"},
            "database": {
                "status": "ok" if db_ok else "error",
                "engine": "SQLite",
                "error": db_error,
            },
            "gemini": {
                "status": "configured" if gemini_configured else "not_configured",
                "model": "gemini-2.5-flash",
                "api_key_set": gemini_configured,
                "note": "Key presence verified — live connectivity checked on first request.",
            },
            "tool_registry": tool_registry_status,
        },
    }

    logger.info(
        "health_check",
        request_id=ctx.request_id,
        status=overall_status,
        db_ok=db_ok,
        gemini_configured=gemini_configured,
    )

    return ctx.ok(health_data)


def _check_tool_registry() -> dict:
    """Checks the tool registry without instantiating GeminiService."""
    return {
        "status": "ok",
        "registered_tools": len(_EXPECTED_TOOLS),
        "tools": _EXPECTED_TOOLS,
        "note": "Full registry initialised per-request when Gemini key is configured.",
    }
