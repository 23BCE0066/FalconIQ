"""
Unit Tests: Phase 3 AI Orchestration Layer

Tests cover:
- WorkflowBuilder: canonical sequences, dependency injection, deduplication, ordering
- ExecutionPlanValidator: registry checks, unregistered tools
- SupervisorAgent: end-to-end orchestration with mock Planner and stub tools
- PlannerAgent: prompt loading, error handling (with mocked GeminiService)
- Health endpoint: DB, registry status
- Chat endpoint: full pipeline with mocked Planner
"""
import asyncio
import sys
import os
from typing import List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.agents.registry import ToolRegistry
from app.agents.workflow.builder import CANONICAL_WORKFLOWS, WorkflowBuilder
from app.constants import AMLPattern, PlannerIntent, RiskLevel, SessionStatus, ToolName
from app.core.dependencies import get_tool_registry
from app.core.exceptions import ToolException, ValidationException
from app.interfaces.tools import BaseTool
from app.schemas.execution_context import ExecutionContext
from app.schemas.execution_plan import ExecutionPlan, FilterParams
from app.schemas.tool_result import ToolResult
from app.services.risk import RiskService
from app.tools.dataset import DatasetTool
from app.tools.explainer import ExplainerTool
from app.tools.feature import FeatureTool
from app.tools.risk_calculator import RiskCalculatorTool
from app.tools.rule_engine import RuleEngineTool
from app.validators.execution_plan import ExecutionPlanValidator


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def full_registry() -> ToolRegistry:
    """Registry with all stub tools registered."""
    from app.tools.ml_engine import MLEngineTool
    from app.tools.network_analyzer import NetworkAnalyzerTool
    from app.services.risk import RiskService
    
    registry = ToolRegistry()
    risk_service = RiskService()
    import pandas as pd
    mock_ds = MagicMock()
    mock_df = pd.DataFrame({
        "transaction_id": ["t1"],
        "sender_id": ["s1"],
        "receiver_id": ["r1"],
        "amount": [100.0],
        "currency": ["USD"],
        "timestamp": ["2026-01-01"],
        "type": ["TRANSFER"],
        "status": ["COMPLETED"],
        "country": ["USA"],
        "is_cross_border": [False],
        "is_weekend": [False],
        "is_night": [False],
    })
    mock_ds.load_transactions.return_value = mock_df
    
    mock_explainer = MagicMock()
    mock_explanation = MagicMock(executive_summary="Summary", detailed_explanation="Details", compliance_recommendation="APPROVE", next_steps=[])
    mock_explanation.model_dump.return_value = {}
    mock_explainer.generate_explanation.return_value = mock_explanation
    
    mock_feature_service = MagicMock()
    mock_feature_service.compute_customer_features.return_value = {"velocity_per_day": 1.0}
    
    registry.register(DatasetTool(dataset_service=mock_ds))
    registry.register(FeatureTool(feature_service=mock_feature_service))
    registry.register(RuleEngineTool())
    registry.register(MLEngineTool(ml_service=MagicMock()))
    registry.register(RiskCalculatorTool(risk_service=risk_service, dataset_service=mock_ds))
    registry.register(ExplainerTool(explainer_service=mock_explainer))
    registry.register(NetworkAnalyzerTool(graph_service=MagicMock()))
    return registry


@pytest.fixture
def workflow_builder() -> WorkflowBuilder:
    return WorkflowBuilder()


@pytest.fixture
def structuring_plan(full_registry: ToolRegistry) -> ExecutionPlan:
    return ExecutionPlan(
        intent=PlannerIntent.STRUCTURING_DETECTION,
        aml_pattern=AMLPattern.STRUCTURING,
        filters=FilterParams(days=30, customer_id="CUST_1"),
        tools=[ToolName.DATASET, ToolName.FEATURE, ToolName.RULE_ENGINE,
               ToolName.RISK_CALCULATOR, ToolName.EXPLAINER],
        confidence=0.95,
        reasoning="Structuring detection requires feature computation and rule evaluation.",
    )


@pytest.fixture
def customer_plan(full_registry: ToolRegistry) -> ExecutionPlan:
    return ExecutionPlan(
        intent=PlannerIntent.CUSTOMER_LOOKUP,
        filters=FilterParams(customer_id="CUST_452"),
        tools=[ToolName.DATASET, ToolName.FEATURE,
               ToolName.RISK_CALCULATOR, ToolName.EXPLAINER],
        confidence=0.98,
        reasoning="Customer investigation: no rules needed, only feature + risk.",
    )


# ── WorkflowBuilder Tests ─────────────────────────────────────────────────────

class TestWorkflowBuilder:
    def test_structuring_detection_workflow(
        self, workflow_builder: WorkflowBuilder, structuring_plan: ExecutionPlan
    ):
        tools = workflow_builder.build(structuring_plan)
        tool_values = [t.value for t in tools]
        assert tool_values[0] == ToolName.DATASET.value, "dataset must be first"
        assert ToolName.FEATURE.value in tool_values
        assert ToolName.RULE_ENGINE.value in tool_values

    def test_customer_lookup_skips_rule_engine(
        self, workflow_builder: WorkflowBuilder, customer_plan: ExecutionPlan
    ):
        tools = workflow_builder.build(customer_plan)
        tool_values = [t.value for t in tools]
        assert ToolName.RULE_ENGINE.value not in tool_values
        assert ToolName.RISK_CALCULATOR.value in tool_values

    def test_dataset_always_first(
        self, workflow_builder: WorkflowBuilder, structuring_plan: ExecutionPlan
    ):
        tools = workflow_builder.build(structuring_plan)
        assert tools[0] == ToolName.DATASET

    def test_risk_calculator_before_explainer(
        self, workflow_builder: WorkflowBuilder, structuring_plan: ExecutionPlan
    ):
        tools = workflow_builder.build(structuring_plan)
        risk_idx = tools.index(ToolName.RISK_CALCULATOR)
        explainer_idx = tools.index(ToolName.EXPLAINER)
        assert risk_idx < explainer_idx

    def test_no_duplicate_tools(
        self, workflow_builder: WorkflowBuilder, structuring_plan: ExecutionPlan
    ):
        tools = workflow_builder.build(structuring_plan)
        assert len(tools) == len(set(tools))

    def test_low_confidence_uses_canonical_fallback(
        self, workflow_builder: WorkflowBuilder
    ):
        low_conf_plan = ExecutionPlan(
            intent=PlannerIntent.STRUCTURING_DETECTION,
            tools=[ToolName.DATASET, ToolName.EXPLAINER],  # Incomplete planner suggestion
            confidence=0.40,  # Below threshold
        )
        tools = workflow_builder.build(low_conf_plan)
        canonical = CANONICAL_WORKFLOWS[PlannerIntent.STRUCTURING_DETECTION]
        assert tools == canonical

    def test_dependency_injection_adds_missing_feature(
        self, workflow_builder: WorkflowBuilder
    ):
        """If rule_engine is requested without feature, feature must be injected."""
        plan = ExecutionPlan(
            intent=PlannerIntent.STRUCTURING_DETECTION,
            tools=[ToolName.DATASET, ToolName.RULE_ENGINE,
                   ToolName.RISK_CALCULATOR, ToolName.EXPLAINER],
            confidence=0.88,
        )
        tools = workflow_builder.build(plan)
        assert ToolName.FEATURE in tools
        feature_idx = tools.index(ToolName.FEATURE)
        rule_idx = tools.index(ToolName.RULE_ENGINE)
        assert feature_idx < rule_idx


# ── ExecutionPlanValidator Tests ──────────────────────────────────────────────

class TestExecutionPlanValidatorPhase3:
    def test_all_registered_tools_pass(
        self, full_registry: ToolRegistry, structuring_plan: ExecutionPlan
    ):
        validator = ExecutionPlanValidator(registry=full_registry)
        validator.validate(structuring_plan)  # Must not raise

    def test_unregistered_tool_fails(self, full_registry: ToolRegistry):
        plan = ExecutionPlan(
            intent=PlannerIntent.GENERAL_INVESTIGATION,
            tools=[ToolName.DATASET, ToolName.FEATURE],
            confidence=0.8,
        )
        # Temporarily remove a tool from registry to simulate unregistered tool
        full_registry.unregister(ToolName.FEATURE.value)
        validator = ExecutionPlanValidator(registry=full_registry)
        with pytest.raises(ValidationException, match="unregistered tools"):
            validator.validate(plan)


# ── Stub Tool Tests ───────────────────────────────────────────────────────────

@pytest.mark.skip(reason="Stub tools replaced by production implementations in Phase 4")
class TestStubTools:
    @pytest.mark.asyncio
    async def test_dataset_tool_succeeds(self):
        tool = DatasetTool()
        ctx = ExecutionContext(query="test query")
        ctx.execution_plan = ExecutionPlan(
            intent=PlannerIntent.STRUCTURING_DETECTION,
            tools=[ToolName.DATASET],
            filters=FilterParams(days=30),
            confidence=0.9,
        )
        result = await tool.execute(ctx)
        assert result.success
        assert result.tool_name == ToolName.DATASET
        assert ctx.get_var("dataset_loaded") is True

    @pytest.mark.asyncio
    async def test_feature_tool_requires_dataset(self):
        tool = FeatureTool()
        ctx = ExecutionContext(query="test query")
        # dataset_loaded NOT set
        result = await tool.execute(ctx)
        assert not result.success
        assert "dataset_loaded" in result.errors[0] or "DatasetTool" in result.errors[0]

    @pytest.mark.asyncio
    async def test_feature_tool_succeeds_after_dataset(self):
        ctx = ExecutionContext(query="test query")
        ctx.set_var("dataset_loaded", True)
        tool = FeatureTool()
        result = await tool.execute(ctx)
        assert result.success
        assert ctx.get_var("features") is not None

    @pytest.mark.asyncio
    async def test_risk_calculator_produces_score(self):
        ctx = ExecutionContext(query="test query")
        ctx.set_var("rule_score", 0.0)
        ctx.set_var("ml_score", None)
        tool = RiskCalculatorTool(risk_service=RiskService())
        result = await tool.execute(ctx)
        assert result.success
        assert "risk_score" in result.data
        assert "risk_level" in result.data
        assert ctx.get_var("risk_score") is not None

    @pytest.mark.asyncio
    async def test_explainer_reads_context(self):
        ctx = ExecutionContext(query="test query")
        ctx.set_var("risk_score", 45.0)
        ctx.set_var("risk_level", "MEDIUM")
        ctx.set_var("rule_results", {"triggered_rules": []})
        tool = ExplainerTool()
        result = await tool.execute(ctx)
        assert result.success
        assert "45.0" in result.data["explanation"]


# ── SupervisorAgent End-to-End Tests ─────────────────────────────────────────

class TestSupervisorAgent:
    @pytest.mark.asyncio
    async def test_full_structuring_pipeline(
        self, full_registry: ToolRegistry, structuring_plan: ExecutionPlan
    ):
        """
        End-to-end test: mock Planner returns a structuring plan,
        Supervisor executes all tools, returns completed ChatResponse.
        """
        from app.agents.supervisor.agent import SupervisorAgent
        from app.agents.workflow.builder import WorkflowBuilder

        # Mock Planner so we don't need a live Gemini API key
        mock_planner = AsyncMock()
        mock_planner.process = AsyncMock(return_value=structuring_plan)

        # Mock SessionRepository (SQLite not needed for this test)
        mock_session_repo = MagicMock()
        mock_session_repo.create_session = MagicMock(return_value=MagicMock())
        mock_session_repo.update_session = MagicMock(return_value=MagicMock())
        mock_session_repo.log_tool_execution = MagicMock(return_value=MagicMock())
        mock_session_repo.mark_session_completed = MagicMock(return_value=MagicMock())
        mock_session_repo.mark_session_failed = MagicMock(return_value=MagicMock())

        supervisor = SupervisorAgent(
            planner=mock_planner,
            workflow_builder=WorkflowBuilder(),
            registry=full_registry,
            session_repo=mock_session_repo,
        )

        response = await supervisor.process("Find structuring patterns in the last 30 days.")

        assert response.status == SessionStatus.COMPLETED
        assert len(response.completed_tools) > 0
        assert len(response.failed_tools) == 0
        assert ToolName.DATASET.value in response.completed_tools
        assert ToolName.FEATURE.value in response.completed_tools
        assert ToolName.EXPLAINER.value in response.completed_tools
        assert response.total_execution_time_ms >= 0
        assert len(response.execution_timeline) > 0

    @pytest.mark.asyncio
    async def test_supervisor_handles_planner_failure(
        self, full_registry: ToolRegistry
    ):
        """Supervisor should return a FAILED response if Planner raises."""
        from app.agents.supervisor.agent import SupervisorAgent
        from app.core.exceptions import PlannerException

        mock_planner = AsyncMock()
        mock_planner.process = AsyncMock(
            side_effect=PlannerException("Gemini API unavailable.")
        )

        mock_session_repo = MagicMock()
        mock_session_repo.create_session = MagicMock(return_value=MagicMock())
        mock_session_repo.update_session = MagicMock(return_value=MagicMock())
        mock_session_repo.mark_session_failed = MagicMock(return_value=MagicMock())

        supervisor = SupervisorAgent(
            planner=mock_planner,
            workflow_builder=WorkflowBuilder(),
            registry=full_registry,
            session_repo=mock_session_repo,
        )

        response = await supervisor.process("Find structuring patterns.")
        assert response.status == SessionStatus.FAILED
        assert len(response.errors) > 0


# ── PlannerAgent Tests ────────────────────────────────────────────────────────

class TestPlannerAgent:
    def test_prompt_loads_from_file(self, full_registry: ToolRegistry):
        """PlannerAgent must load prompt from prompts/planner.md successfully."""
        from app.agents.planner.agent import PlannerAgent
        from app.validators.execution_plan import ExecutionPlanValidator

        mock_gemini = MagicMock()
        validator = ExecutionPlanValidator(registry=full_registry)
        agent = PlannerAgent(gemini=mock_gemini, validator=validator)
        # If the file loaded correctly, system_prompt will be non-empty
        assert len(agent._system_prompt) > 100

    def test_prompt_missing_raises_planner_exception(self, full_registry: ToolRegistry, tmp_path):
        """PlannerAgent must raise PlannerException if prompt file is missing."""
        from app.agents.planner import agent as planner_module
        from app.agents.planner.agent import PlannerAgent
        from app.core.exceptions import PlannerException
        from app.validators.execution_plan import ExecutionPlanValidator

        original_path = planner_module._PROMPT_PATH
        try:
            planner_module._PROMPT_PATH = tmp_path / "nonexistent.md"
            with pytest.raises(PlannerException, match="not found"):
                PlannerAgent(
                    gemini=MagicMock(),
                    validator=ExecutionPlanValidator(registry=full_registry),
                )
        finally:
            planner_module._PROMPT_PATH = original_path


# ── Health Endpoint Tests ─────────────────────────────────────────────────────

class TestHealthEndpoint:
    @pytest.fixture(autouse=True)
    def mock_env(self):
        os.environ["GEMINI_API_KEY"] = "mock_key"
        yield
        os.environ.pop("GEMINI_API_KEY", None)

    def test_health_returns_ok_structure(self):
        """Health endpoint must return the correct subsystem structure."""
        from app.main import app
        from app.core.dependencies import get_gemini_service
        from unittest.mock import MagicMock

        app.dependency_overrides[get_gemini_service] = lambda: MagicMock()
        
        with TestClient(app) as client:
            response = client.get("/api/v1/health")
            
        app.dependency_overrides.clear()
        assert response.status_code == 200
        data = response.json()
        # Phase 5: response is now wrapped in standard ResponseEnvelope
        assert data["success"] is True
        payload = data["data"]
        assert "status" in payload
        assert "subsystems" in payload
        assert "database" in payload["subsystems"]
        assert "gemini" in payload["subsystems"]
        assert "tool_registry" in payload["subsystems"]

    def test_health_tool_registry_populated(self):
        """Health endpoint must report all registered tools."""
        from app.main import app
        from app.core.dependencies import get_gemini_service
        from unittest.mock import MagicMock

        app.dependency_overrides[get_gemini_service] = lambda: MagicMock()

        with TestClient(app) as client:
            response = client.get("/api/v1/health")
            
        app.dependency_overrides.clear()
        data = response.json()
        # Phase 5: data is wrapped in envelope — access via data["data"]
        payload = data["data"]
        tool_registry = payload["subsystems"]["tool_registry"]
        assert tool_registry["registered_tools"] >= 5
        # Phase 5 health uses static tool list — check known tool names
        known_tools = ["dataset", "feature", "rule_engine", "ml_engine",
                       "risk_calculator", "explainer", "network_analyzer"]
        for tool in tool_registry["tools"]:
            assert tool in known_tools

    def test_health_database_connected(self):
        """Health endpoint must confirm database connectivity."""
        from app.main import app
        from app.core.dependencies import get_gemini_service
        from unittest.mock import MagicMock

        app.dependency_overrides[get_gemini_service] = lambda: MagicMock()

        with TestClient(app) as client:
            response = client.get("/api/v1/health")
            
        app.dependency_overrides.clear()
        data = response.json()
        # Phase 5: data is wrapped in envelope — access via data["data"]
        payload = data["data"]
        assert payload["subsystems"]["database"]["status"] == "ok"
