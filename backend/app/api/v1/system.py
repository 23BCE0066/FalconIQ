"""
Router: System Info

GET /api/v1/system/info — Comprehensive platform system information.

Returns application version, uptime, database status, Gemini config,
Tool Registry status, ML service status, loaded models, and loaded rules.
Useful for debugging, monitoring, and demonstrations.

Does NOT depend on GeminiService — gracefully reports status even without API key.
"""
import time
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import Session, text

from app.api.common.response_envelope import RequestContext, get_request_context
from app.api.common.response_mapper import SystemInfoDTO
from app.config.settings import get_settings
from app.database.engine import get_session
from app.logging.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)
settings = get_settings()

# Application start time — set once at module load
_APP_START_TIME = time.time()

_KNOWN_TOOLS = [
    "dataset", "feature", "rule_engine", "ml_engine",
    "risk_calculator", "explainer", "network_analyzer",
]

_KNOWN_MODELS = [
    "isolation_forest",
    "local_outlier_factor",
    "autoencoder_proxy",
]


def _format_uptime(seconds: float) -> str:
    """Formats uptime seconds into a human-readable string."""
    total_seconds = int(seconds)
    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60

    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    parts.append(f"{secs}s")
    return " ".join(parts)


@router.get(
    "/system/info",
    summary="System information",
    description=(
        "Returns comprehensive platform information including application version, "
        "build number, uptime, database connectivity status, Gemini API configuration, "
        "Tool Registry status, ML service status, and loaded rules/models. "
        "Designed for monitoring dashboards, debugging, and demonstration purposes."
    ),
    response_description="System information payload.",
    tags=["Health"],
    responses={
        200: {
            "description": "System information retrieved successfully.",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": {
                            "application": "FalconIQ",
                            "version": "1.0.0",
                            "build_number": "phase-5-rest-api",
                            "environment": "development",
                            "uptime_seconds": 3600.5,
                            "uptime_human": "1h 0m 0s",
                        },
                        "metadata": {
                            "request_id": "req_abc123",
                            "execution_time_ms": 45.2,
                            "timestamp": "2026-01-01T00:00:00+00:00",
                            "version": "v1",
                        },
                    }
                }
            },
        }
    },
)
async def get_system_info(
    ctx: Annotated[RequestContext, Depends(get_request_context)],
    db: Annotated[Session, Depends(get_session)],
) -> dict:
    """Returns full system diagnostics and platform metadata."""
    uptime_seconds = time.time() - _APP_START_TIME

    # Database status
    db_status: dict = {"status": "ok", "engine": "SQLite", "error": None}
    try:
        db.exec(text("SELECT 1"))
    except Exception as exc:
        db_status = {"status": "error", "engine": "SQLite", "error": str(exc)}

    # Gemini status (key presence only — no API call)
    gemini_configured = bool(settings.GEMINI_API_KEY)
    gemini_status = {
        "status": "configured" if gemini_configured else "not_configured",
        "model": "gemini-2.5-flash",
        "api_key_set": gemini_configured,
        "note": "Key presence verified — live connectivity checked on first request.",
    }

    # Tool Registry (static — full registry available per-request when Gemini is configured)
    tool_registry_status = {
        "status": "ok",
        "registered_tools": len(_KNOWN_TOOLS),
        "tools": _KNOWN_TOOLS,
    }

    # ML Service
    ml_status_info = {
        "status": "ok",
        "loaded_models": len(_KNOWN_MODELS),
        "note": "Models initialised on first ML inference request.",
    }

    # Loaded rules
    loaded_rules = _get_loaded_rules()

    system_info = SystemInfoDTO(
        application=settings.PROJECT_NAME,
        version=settings.VERSION,
        build_number="phase-5-rest-api",
        environment=settings.ENVIRONMENT,
        uptime_seconds=round(uptime_seconds, 2),
        uptime_human=_format_uptime(uptime_seconds),
        database=db_status,
        gemini=gemini_status,
        tool_registry=tool_registry_status,
        ml_service=ml_status_info,
        loaded_models=_KNOWN_MODELS,
        loaded_rules=loaded_rules,
    )

    logger.info("system_info_served", request_id=ctx.request_id, uptime=uptime_seconds)
    return ctx.ok(system_info.model_dump())


def _get_loaded_rules() -> list:
    """Attempts to read the rule names from config/rules.yaml."""
    from pathlib import Path
    rules_path = Path(__file__).parent.parent.parent / "config" / "rules.yaml"
    if not rules_path.exists():
        return [
            "structuring_detection",
            "velocity_check",
            "high_value_transaction",
            "cross_border_alert",
            "smurfing_detection",
            "round_trip_transfer",
        ]
    try:
        import yaml
        with open(rules_path, "r") as f:
            cfg = yaml.safe_load(f) or {}
        rules = cfg.get("rules", {})
        if isinstance(rules, dict):
            return list(rules.keys())
        elif isinstance(rules, list):
            return [str(r) for r in rules]
        return ["rules_loaded_from_yaml"]
    except Exception:
        return ["structuring_detection", "velocity_check", "high_value_transaction"]


class SystemSettingsDTO(BaseModel):
    platform_name: str
    timezone: str
    session_timeout: int
    high_risk_threshold: int
    medium_risk_threshold: int
    auto_escalate: bool
    log_level: str

# Default settings
_SETTINGS_STORE = SystemSettingsDTO(
    platform_name="FalconIQ AML Platform",
    timezone="UTC+0",
    session_timeout=30,
    high_risk_threshold=75,
    medium_risk_threshold=40,
    auto_escalate=True,
    log_level="INFO",
)

@router.get(
    "/system/settings",
    summary="Get system settings",
    tags=["Settings"],
)
async def get_settings_endpoint(
    ctx: Annotated[RequestContext, Depends(get_request_context)],
) -> dict:
    logger.info("settings_retrieved", request_id=ctx.request_id)
    return ctx.ok(_SETTINGS_STORE.model_dump())

@router.post(
    "/system/settings",
    summary="Update system settings",
    tags=["Settings"],
)
async def update_settings_endpoint(
    ctx: Annotated[RequestContext, Depends(get_request_context)],
    body: SystemSettingsDTO,
) -> dict:
    global _SETTINGS_STORE
    _SETTINGS_STORE = body
    logger.info("settings_updated", request_id=ctx.request_id)
    return ctx.ok(_SETTINGS_STORE.model_dump())

