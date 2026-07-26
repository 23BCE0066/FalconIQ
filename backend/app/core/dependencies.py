"""
Dependency Injection: Service providers for FastAPI routes.

All injected dependencies are created here — never inside routers or tools.
Using @lru_cache for singletons that are safe to share across requests
(stateless services like Gemini). Session-scoped objects (repositories, tools)
are created per-request.
"""
from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlmodel import Session

from app.agents.planner.agent import PlannerAgent
from app.agents.registry import ToolRegistry
from app.agents.supervisor.agent import SupervisorAgent
from app.agents.workflow.builder import WorkflowBuilder
from app.config.settings import get_settings
from app.database.engine import get_session
from app.repository.alert import AlertRepository
from app.repository.customer import CustomerRepository
from app.repository.session import SessionRepository
from app.repository.transaction import TransactionRepository
from app.services.alert import AlertService
from app.services.analytics import AnalyticsService
from app.services.customer import CustomerService
from app.services.dashboard import DashboardService
from app.services.dataset import DatasetService
from app.services.explainer import ExplainerService
from app.services.feature import FeatureService
from app.services.gemini import GeminiService
from app.services.graph import GraphService
from app.services.ml import MLService
from app.services.report import ReportService
from app.services.risk import RiskService
from app.services.statistics import StatisticsService
from app.services.transaction import TransactionService
from app.tools.dataset import DatasetTool
from app.tools.explainer import ExplainerTool
from app.tools.feature import FeatureTool
from app.tools.ml_engine import MLEngineTool
from app.tools.network_analyzer import NetworkAnalyzerTool
from app.tools.risk_calculator import RiskCalculatorTool
from app.tools.rule_engine import RuleEngineTool
from app.validators.execution_plan import ExecutionPlanValidator

# ── Singletons (created once at startup) ──────────────────────────────────────

@lru_cache()
def get_gemini_service() -> GeminiService:
    settings = get_settings()
    return GeminiService(api_key=settings.GEMINI_API_KEY)


@lru_cache()
def get_risk_service() -> RiskService:
    return RiskService()


@lru_cache()
def get_feature_service() -> FeatureService:
    return FeatureService()


@lru_cache()
def get_ml_service() -> MLService:
    return MLService()


@lru_cache()
def get_graph_service() -> GraphService:
    return GraphService()


@lru_cache()
def get_explainer_service(
    gemini: Annotated[GeminiService, Depends(get_gemini_service)]
) -> ExplainerService:
    return ExplainerService(gemini_service=gemini)


@lru_cache()
def get_workflow_builder() -> WorkflowBuilder:
    return WorkflowBuilder()


# ── Per-Request Dependencies ───────────────────────────────────────────────────

DBSession = Annotated[Session, Depends(get_session)]


def get_session_repository(db: DBSession) -> SessionRepository:
    return SessionRepository(session=db)


def get_customer_repository(db: DBSession) -> CustomerRepository:
    return CustomerRepository(session=db)


def get_alert_repository(db: DBSession) -> AlertRepository:
    return AlertRepository(session=db)


def get_transaction_repository(db: DBSession) -> TransactionRepository:
    return TransactionRepository(session=db)


def get_customer_service(
    repo: Annotated[CustomerRepository, Depends(get_customer_repository)],
) -> CustomerService:
    return CustomerService(repository=repo)


def get_alert_service(
    repo: Annotated[AlertRepository, Depends(get_alert_repository)],
) -> AlertService:
    return AlertService(repository=repo)


def get_dataset_service(
    tx_repo: Annotated[TransactionRepository, Depends(get_transaction_repository)],
    cust_repo: Annotated[CustomerRepository, Depends(get_customer_repository)],
) -> DatasetService:
    return DatasetService(transaction_repo=tx_repo, customer_repo=cust_repo)


def get_tool_registry(
    dataset_service: Annotated[DatasetService, Depends(get_dataset_service)],
    feature_service: Annotated[FeatureService, Depends(get_feature_service)],
    ml_service: Annotated[MLService, Depends(get_ml_service)],
    risk_service: Annotated[RiskService, Depends(get_risk_service)],
    explainer_service: Annotated[ExplainerService, Depends(get_explainer_service)],
    graph_service: Annotated[GraphService, Depends(get_graph_service)],
) -> ToolRegistry:
    """
    Creates a ToolRegistry per request.
    Tools require request-scoped services (like DatasetService, which needs a DB session).
    """
    registry = ToolRegistry()
    registry.register(DatasetTool(dataset_service=dataset_service))
    registry.register(FeatureTool(feature_service=feature_service))
    registry.register(RuleEngineTool())
    registry.register(MLEngineTool(ml_service=ml_service))
    registry.register(RiskCalculatorTool(risk_service=risk_service, dataset_service=dataset_service))
    registry.register(ExplainerTool(explainer_service=explainer_service))
    registry.register(NetworkAnalyzerTool(graph_service=graph_service))
    return registry


def get_execution_plan_validator(
    registry: Annotated[ToolRegistry, Depends(get_tool_registry)],
) -> ExecutionPlanValidator:
    return ExecutionPlanValidator(registry=registry)


def get_planner_agent(
    gemini: Annotated[GeminiService, Depends(get_gemini_service)],
    validator: Annotated[ExecutionPlanValidator, Depends(get_execution_plan_validator)],
) -> PlannerAgent:
    return PlannerAgent(gemini=gemini, validator=validator)


def get_supervisor_agent(
    planner: Annotated[PlannerAgent, Depends(get_planner_agent)],
    workflow_builder: Annotated[WorkflowBuilder, Depends(get_workflow_builder)],
    registry: Annotated[ToolRegistry, Depends(get_tool_registry)],
    session_repo: Annotated[SessionRepository, Depends(get_session_repository)],
) -> SupervisorAgent:
    return SupervisorAgent(
        planner=planner,
        workflow_builder=workflow_builder,
        registry=registry,
        session_repo=session_repo,
    )


# ── Phase 5: New Service Providers ────────────────────────────────────────────

def get_transaction_service(
    repo: Annotated[TransactionRepository, Depends(get_transaction_repository)],
    db: DBSession,
) -> TransactionService:
    """Per-request TransactionService with pagination and filter support."""
    return TransactionService(repository=repo, session=db)


def get_statistics_service(db: DBSession) -> StatisticsService:
    """Per-request StatisticsService — the single source for all aggregations."""
    return StatisticsService(session=db)


def get_dashboard_service(
    stats: Annotated[StatisticsService, Depends(get_statistics_service)],
) -> DashboardService:
    """Per-request DashboardService."""
    return DashboardService(statistics=stats)


def get_analytics_service(
    stats: Annotated[StatisticsService, Depends(get_statistics_service)],
    db: DBSession,
) -> AnalyticsService:
    """Per-request AnalyticsService."""
    return AnalyticsService(statistics=stats, session=db)


def get_report_service(
    stats: Annotated[StatisticsService, Depends(get_statistics_service)],
    db: DBSession,
) -> ReportService:
    """Per-request ReportService."""
    return ReportService(statistics=stats, session=db)
