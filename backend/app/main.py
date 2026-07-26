"""
FalconIQ FastAPI Application Entry Point

Startup sequence:
1. Configure structured logging.
2. Pre-warm singleton dependencies (ToolRegistry, GeminiService, RiskService).
3. Initialise SQLite database (create tables).
4. Mount middleware (CORS, RequestID, Logging).
5. Register all exception handlers via common module.
6. Mount all API v1 routers.

Phase 5 Additions:
    - All 9 API group routers registered.
    - Centralised exception handlers from app.api.common.exceptions.
    - System info endpoint under /api/v1/system.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import all SQLModel models before init_db() so metadata is populated
import app.database.models  # noqa: F401

# API v1 routers
from app.api.v1 import (
    alerts,
    analytics,
    chat,
    customers,
    dashboard,
    health,
    investigations,
    network,
    reports,
    system,
    transactions,
)
from app.api.common.exceptions import register_exception_handlers
from app.config.settings import get_settings
from app.core.dependencies import get_gemini_service, get_tool_registry
from app.database.engine import init_db
from app.logging.logger import setup_logging
from app.middleware.logging import LoggingMiddleware, RequestIDMiddleware

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and (optional) shutdown logic."""
    # Startup
    setup_logging(debug=settings.DEBUG)

    # Initialise database tables
    init_db()

    # Pre-warm GeminiService if key is set (CI/test environments skip this)
    if settings.GEMINI_API_KEY:
        get_gemini_service()

    yield
    # Shutdown: nothing to clean up for SQLite monolith


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "**FalconIQ** — Enterprise AI-Powered AML Investigation Platform.\n\n"
        "Submit natural language queries to trigger dynamic compliance investigations "
        "powered by Gemini AI, ML anomaly detection, and an intelligent rule engine.\n\n"
        "**API Groups:**\n"
        "- `Dashboard` — Platform KPIs and visualization-ready metrics\n"
        "- `Customers` — Customer profiles, risk breakdowns, and event timelines\n"
        "- `Transactions` — Transaction list, search, and detail\n"
        "- `Alerts` — Compliance alert management with HITL workflow\n"
        "- `Analytics` — Risk, trends, rules, country, and customer analytics\n"
        "- `Reports` — Generate and download compliance reports\n"
        "- `Network` — Transaction network graph analysis\n"
        "- `Chat` — AI-powered natural language investigation\n"
        "- `Health` — Platform health and system information\n"
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "Dashboard", "description": "Platform KPIs and visualization-ready dashboard metrics."},
        {"name": "Customers", "description": "Customer profiles, risk analysis, and event timelines."},
        {"name": "Transactions", "description": "Transaction list, search, and detail views."},
        {"name": "Alerts", "description": "Compliance alert management with Human-in-the-Loop workflow."},
        {"name": "Analytics", "description": "Risk, trend, rule, country, and customer analytics."},
        {"name": "Reports", "description": "Generate and download compliance reports (JSON, Markdown, PDF)."},
        {"name": "Network", "description": "Transaction network graph analysis for AML typology detection."},
        {"name": "Chat", "description": "AI-powered natural language AML investigation endpoint."},
        {"name": "Health", "description": "Platform health checks and system information."},
    ],
    lifespan=lifespan,
)

# ── Middleware (order: outermost first) ────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(LoggingMiddleware)
app.add_middleware(RequestIDMiddleware)

# ── Exception Handlers (replaces inline global_exception_handler) ──────────────
register_exception_handlers(app)

import os
from fastapi.staticfiles import StaticFiles

# ── API v1 Routers ─────────────────────────────────────────────────────────────
_PREFIX = settings.API_V1_STR  # /api/v1

app.include_router(health.router,       prefix=_PREFIX, tags=["Health"])
app.include_router(system.router,       prefix=_PREFIX, tags=["Health"])
app.include_router(dashboard.router,    prefix=_PREFIX, tags=["Dashboard"])
app.include_router(customers.router,    prefix=_PREFIX, tags=["Customers"])
app.include_router(transactions.router, prefix=_PREFIX, tags=["Transactions"])
app.include_router(alerts.router,       prefix=_PREFIX, tags=["Alerts"])
app.include_router(analytics.router,    prefix=_PREFIX, tags=["Analytics"])
app.include_router(reports.router,      prefix=_PREFIX, tags=["Reports"])
app.include_router(network.router,      prefix=_PREFIX, tags=["Network"])
app.include_router(chat.router,         prefix=_PREFIX, tags=["Chat"])
app.include_router(investigations.router, prefix=_PREFIX, tags=["Investigations"])

# ── Static Files (Frontend) ────────────────────────────────────────────────────
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend"))
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
