"""
Unit Tests: Phase 2 Core Framework

Covers:
- ExecutionContext state management
- ToolRegistry registration and resolution
- ToolResult factory methods
- ExecutionPlanValidator
- ToolResultValidator / DatasetValidator
- RiskService scoring logic
"""
import sys
import os

# Ensure backend root is on the path when running from tests/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import pandas as pd

from app.agents.registry import ToolRegistry
from app.constants import (
    AMLPattern,
    KYCStatus,
    PlannerIntent,
    RiskLevel,
    SessionStatus,
    ToolName,
)
from app.core.exceptions import ToolException, ValidationException
from app.interfaces.tools import BaseTool
from app.schemas.chat import ChatRequest
from app.schemas.execution_context import ExecutionContext
from app.schemas.execution_plan import ExecutionPlan, FilterParams
from app.schemas.tool_result import ToolResult
from app.services.risk import RiskService
from app.validators.execution_plan import ExecutionPlanValidator
from app.validators.tool_result import DatasetValidator, ToolResultValidator


# ── Fixtures ──────────────────────────────────────────────────────────────────

class MockDatasetTool(BaseTool):
    @property
    def name(self) -> str:
        return ToolName.DATASET

    @property
    def description(self) -> str:
        return "Mock dataset tool for testing."

    async def _run(self, context: ExecutionContext) -> ToolResult:
        return ToolResult(
            success=True,
            status="completed",
            tool_name=self.name,
            execution_time_ms=10.0,
            confidence=0.95,
            data={"rows": 100},
            explanation="Loaded 100 rows.",
        )


class MockFeatureTool(BaseTool):
    @property
    def name(self) -> str:
        return ToolName.FEATURE

    @property
    def description(self) -> str:
        return "Mock feature tool."

    async def _run(self, context: ExecutionContext) -> ToolResult:
        return ToolResult(
            success=True,
            status="completed",
            tool_name=self.name,
            execution_time_ms=5.0,
            confidence=1.0,
            data={"features_computed": 15},
            explanation="Computed 15 features.",
        )


@pytest.fixture
def registry() -> ToolRegistry:
    reg = ToolRegistry()
    reg.register(MockDatasetTool())
    reg.register(MockFeatureTool())
    return reg


@pytest.fixture
def context() -> ExecutionContext:
    return ExecutionContext(query="Find structuring patterns in the last 30 days.")


@pytest.fixture
def valid_plan(registry: ToolRegistry) -> ExecutionPlan:
    return ExecutionPlan(
        intent=PlannerIntent.STRUCTURING_DETECTION,
        aml_pattern=AMLPattern.STRUCTURING,
        filters=FilterParams(days=30),
        tools=[ToolName.DATASET, ToolName.FEATURE],
        confidence=0.92,
        reasoning="User requested structuring detection — load data then compute features.",
    )


# ── ExecutionContext Tests ─────────────────────────────────────────────────────

class TestExecutionContext:
    def test_initial_status_is_running(self, context: ExecutionContext):
        assert context.status == SessionStatus.RUNNING

    def test_set_and_get_variable(self, context: ExecutionContext):
        context.set_var("risk_score", 87.5)
        assert context.get_var("risk_score") == 87.5

    def test_get_missing_variable_returns_default(self, context: ExecutionContext):
        assert context.get_var("nonexistent", default="fallback") == "fallback"

    def test_dataframe_cache(self, context: ExecutionContext):
        df = pd.DataFrame({"amount": [100, 200, 300]})
        context.set_df("transactions", df)
        assert context.has_df("transactions")
        retrieved = context.get_df("transactions")
        assert retrieved is not None
        assert len(retrieved) == 3

    def test_missing_df_returns_none(self, context: ExecutionContext):
        assert context.get_df("missing_key") is None

    def test_record_successful_tool_result(self, context: ExecutionContext):
        result = ToolResult(
            success=True, status="completed", tool_name="dataset",
            execution_time_ms=12.0, confidence=0.9,
            data={"rows": 500}, explanation="Loaded data."
        )
        context.record_tool_result(result)
        assert "dataset" in context.completed_tools
        assert "dataset" not in context.failed_tools
        assert context.current_step == 1

    def test_record_failed_tool_result(self, context: ExecutionContext):
        result = ToolResult.failure("rule_engine", "Database connection failed.")
        context.record_tool_result(result)
        assert "rule_engine" in context.failed_tools
        assert context.has_hard_failures()

    def test_mark_completed(self, context: ExecutionContext):
        context.mark_completed()
        assert context.status == SessionStatus.COMPLETED
        assert context.completed_at is not None

    def test_mark_failed(self, context: ExecutionContext):
        context.mark_failed("Planner returned invalid JSON.")
        assert context.status == SessionStatus.FAILED
        assert "Planner returned invalid JSON." in context.errors

    def test_total_elapsed_ms_is_positive(self, context: ExecutionContext):
        elapsed = context.total_elapsed_ms()
        assert elapsed >= 0.0


# ── ToolRegistry Tests ────────────────────────────────────────────────────────

class TestToolRegistry:
    def test_register_and_get(self, registry: ToolRegistry):
        tool = registry.get(ToolName.DATASET)
        assert tool.name == ToolName.DATASET

    def test_exists_returns_true_for_registered(self, registry: ToolRegistry):
        assert registry.exists(ToolName.DATASET)

    def test_exists_returns_false_for_unknown(self, registry: ToolRegistry):
        assert not registry.exists("nonexistent_tool")

    def test_get_raises_for_unknown_tool(self, registry: ToolRegistry):
        with pytest.raises(ToolException, match="not found in registry"):
            registry.get("nonexistent_tool")

    def test_register_duplicate_raises(self, registry: ToolRegistry):
        with pytest.raises(ToolException, match="already registered"):
            registry.register(MockDatasetTool())

    def test_unregister(self, registry: ToolRegistry):
        registry.unregister(ToolName.FEATURE)
        assert not registry.exists(ToolName.FEATURE)

    def test_list_tools(self, registry: ToolRegistry):
        tools = registry.list_tools()
        assert ToolName.DATASET in tools
        assert ToolName.FEATURE in tools

    def test_get_descriptions_returns_dict(self, registry: ToolRegistry):
        descs = registry.get_descriptions()
        assert ToolName.DATASET in descs
        assert isinstance(descs[ToolName.DATASET], str)


# ── ToolResult Tests ──────────────────────────────────────────────────────────

class TestToolResult:
    def test_failure_factory(self):
        result = ToolResult.failure("rule_engine", "Threshold config missing.")
        assert not result.success
        assert result.status == "failed"
        assert result.confidence == 0.0
        assert "Threshold config missing." in result.errors

    def test_skipped_factory(self):
        result = ToolResult.skipped("eda", "EDA not required for this intent.")
        assert result.success
        assert result.status == "skipped"
        assert result.execution_time_ms == 0.0


# ── ExecutionPlanValidator Tests ──────────────────────────────────────────────

class TestExecutionPlanValidator:
    def test_valid_plan_passes(self, registry: ToolRegistry, valid_plan: ExecutionPlan):
        validator = ExecutionPlanValidator(registry)
        validator.validate(valid_plan)  # Should not raise

    def test_empty_tools_raises(self, registry: ToolRegistry):
        with pytest.raises(Exception):
            # Pydantic min_length=1 will raise at model creation
            ExecutionPlan(
                intent=PlannerIntent.EDA_REQUEST,
                tools=[],
                confidence=0.8,
            )

    def test_unregistered_tool_raises(self, registry: ToolRegistry):
        plan = ExecutionPlan(
            intent=PlannerIntent.GENERAL_INVESTIGATION,
            tools=[ToolName.DATASET, ToolName.ML_ENGINE],  # ml_engine not registered
            confidence=0.7,
        )
        validator = ExecutionPlanValidator(registry)
        with pytest.raises(ValidationException, match="unregistered tools"):
            validator.validate(plan)


# ── ToolResultValidator Tests ─────────────────────────────────────────────────

class TestToolResultValidator:
    def test_valid_result_passes(self):
        result = ToolResult(
            success=True, status="completed", tool_name="dataset",
            execution_time_ms=50.0, confidence=0.88,
            data={}, explanation="OK"
        )
        ToolResultValidator().validate(result)  # Should not raise

    def test_failure_without_error_raises(self):
        result = ToolResult(
            success=False, status="failed", tool_name="ml_engine",
            execution_time_ms=10.0, confidence=0.0, data={}, explanation=""
        )
        # errors list is empty on a manually created failure
        with pytest.raises(ValidationException, match="no error messages"):
            ToolResultValidator().validate(result)


# ── DatasetValidator Tests ────────────────────────────────────────────────────

class TestDatasetValidator:
    def test_valid_df_passes(self):
        df = pd.DataFrame({
            "transaction_id": ["t1"],
            "sender_id": ["c1"],
            "receiver_id": ["c2"],
            "amount": [500.0],
            "timestamp": ["2024-01-01"],
            "type": ["TRANSFER"],
            "country": ["USA"],
        })
        DatasetValidator().validate_transaction_df(df)  # Should not raise

    def test_empty_df_raises(self):
        df = pd.DataFrame()
        with pytest.raises(ValidationException, match="empty"):
            DatasetValidator().validate_transaction_df(df)

    def test_missing_column_raises(self):
        df = pd.DataFrame({"sender_id": ["c1"], "amount": [100.0]})
        with pytest.raises(ValidationException, match="missing required columns"):
            DatasetValidator().validate_transaction_df(df)


# ── RiskService Tests ─────────────────────────────────────────────────────────

class TestRiskService:
    def test_low_risk_score(self):
        svc = RiskService()
        score = svc.compute_composite_score(
            kyc_status=KYCStatus.VERIFIED,
            customer_risk=RiskLevel.LOW,
            rule_score=0.0,
            ml_score=0.0,
            behaviour_score=0.0,
            country_score=0.0,
        )
        assert 0.0 <= score <= 35.0

    def test_high_risk_score(self):
        svc = RiskService()
        score = svc.compute_composite_score(
            kyc_status=KYCStatus.FAILED,
            customer_risk=RiskLevel.HIGH,
            rule_score=70.0,
            ml_score=80.0,
            behaviour_score=50.0,
            country_score=50.0,
        )
        assert score > 65.0

    def test_classify_low(self):
        svc = RiskService()
        assert svc.classify_risk(10.0) == RiskLevel.LOW

    def test_classify_medium(self):
        svc = RiskService()
        assert svc.classify_risk(50.0) == RiskLevel.MEDIUM

    def test_classify_high(self):
        svc = RiskService()
        assert svc.classify_risk(75.0) == RiskLevel.HIGH

    def test_classify_critical(self):
        svc = RiskService()
        assert svc.classify_risk(90.0) == RiskLevel.CRITICAL

    def test_score_capped_at_100(self):
        svc = RiskService()
        score = svc.compute_composite_score(
            kyc_status=KYCStatus.FAILED,
            customer_risk=RiskLevel.CRITICAL,
            rule_score=100.0,
            ml_score=100.0,
            behaviour_score=100.0,
            country_score=100.0,
        )
        assert score <= 100.0
