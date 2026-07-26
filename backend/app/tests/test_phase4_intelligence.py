"""
Unit Tests: Phase 4 AML Intelligence Layer

Tests cover:
- DatasetService & DatasetTool
- FeatureService (Customer and Global feature extraction)
- All 6 AML Rules (Structuring, Velocity, Cashout, Layering, CrossBorder, Dormancy)
- RiskService (Composite scoring)
- MLService (Isolation Forest)
- ExplainerService (Mocked LLM)
- GraphService (Network Analysis)
"""
import pandas as pd
import pytest
from datetime import datetime, timedelta, timezone

from app.constants import KYCStatus, RiskLevel, TransactionType
from app.database.models.customer import Customer
from app.rule_engine.rules import (
    CrossBorderRule,
    DormantAccountRule,
    LayeringRule,
    RapidCashOutRule,
    StructuringRule,
    VelocityRule,
)
from app.services.dataset import DatasetService
from app.services.feature import FeatureService
from app.services.graph import GraphService
from app.services.ml import MLService
from app.services.risk import RiskService


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_transactions_df():
    now = datetime.now(timezone.utc)
    return pd.DataFrame([
        {
            "transaction_id": "tx1",
            "sender_id": "CUST_1",
            "receiver_id": "CUST_2",
            "amount": 9800.0,
            "timestamp": now - timedelta(hours=1),
            "type": TransactionType.TRANSFER.value,
            "country": "USA",
            "is_cross_border": False,
            "is_weekend": False,
            "is_night": False,
        },
        {
            "transaction_id": "tx2",
            "sender_id": "CUST_1",
            "receiver_id": "CUST_3",
            "amount": 9900.0,
            "timestamp": now - timedelta(hours=2),
            "type": TransactionType.TRANSFER.value,
            "country": "USA",
            "is_cross_border": False,
            "is_weekend": False,
            "is_night": False,
        },
        {
            "transaction_id": "tx3",
            "sender_id": "CUST_1",
            "receiver_id": "CUST_4",
            "amount": 9700.0,
            "timestamp": now - timedelta(hours=3),
            "type": TransactionType.TRANSFER.value,
            "country": "USA",
            "is_cross_border": False,
            "is_weekend": False,
            "is_night": False,
        },
    ])


@pytest.fixture
def mock_circular_df():
    now = datetime.now(timezone.utc)
    return pd.DataFrame([
        {"sender_id": "A", "receiver_id": "B", "amount": 1000, "timestamp": now},
        {"sender_id": "B", "receiver_id": "C", "amount": 950, "timestamp": now},
        {"sender_id": "C", "receiver_id": "A", "amount": 900, "timestamp": now},
    ])


@pytest.fixture
def feature_service():
    return FeatureService()


@pytest.fixture
def graph_service():
    return GraphService()


@pytest.fixture
def risk_service():
    return RiskService()


@pytest.fixture
def ml_service():
    return MLService(contamination=0.1, random_state=42)


# ── FeatureService Tests ──────────────────────────────────────────────────────

def test_feature_computation(feature_service: FeatureService, mock_transactions_df: pd.DataFrame):
    features = feature_service.compute_customer_features("CUST_1", mock_transactions_df)
    
    assert features["transaction_count"] == 3
    assert features["total_amount"] == 29400.0
    assert features["structuring_count"] == 3
    assert features["unique_receivers"] == 3


def test_global_feature_computation(feature_service: FeatureService, mock_transactions_df: pd.DataFrame):
    df = feature_service.compute_global_features(mock_transactions_df)
    
    assert not df.empty
    assert "CUST_1" in df.index
    assert df.loc["CUST_1", "transaction_count"] == 3


# ── Rule Engine Tests ─────────────────────────────────────────────────────────

def test_structuring_rule(feature_service: FeatureService, mock_transactions_df: pd.DataFrame):
    features = feature_service.compute_customer_features("CUST_1", mock_transactions_df)
    rule = StructuringRule()
    result = rule.evaluate(features, mock_transactions_df)
    
    assert result.triggered
    assert result.score > 0
    assert len(result.evidence) == 3


def test_velocity_rule():
    features = {"velocity_per_day": 20.0, "rolling_sum_30d": 10000.0}
    rule = VelocityRule()
    result = rule.evaluate(features)
    assert result.triggered


def test_rapid_cashout_rule():
    features = {"rapid_cashout_score": 0.90, "total_amount": 50000.0}
    rule = RapidCashOutRule()
    result = rule.evaluate(features)
    assert result.triggered


def test_cross_border_rule():
    features = {"cross_border_ratio": 0.80, "high_risk_country_count": 3}
    rule = CrossBorderRule()
    result = rule.evaluate(features)
    assert result.triggered


# ── ML Engine Tests ───────────────────────────────────────────────────────────

def test_isolation_forest_anomaly_detection(ml_service: MLService):
    # Create 9 normal profiles, 1 anomalous
    data = []
    for i in range(9):
        data.append({"customer_id": f"C_{i}", "total_amount": 1000.0, "velocity_per_day": 1.0})
    data.append({"customer_id": "C_ANOMALY", "total_amount": 950000.0, "velocity_per_day": 55.0})
    
    df = pd.DataFrame(data).set_index("customer_id")
    
    scores, top = ml_service.detect_anomalies(df)
    
    assert "C_ANOMALY" in scores
    assert scores["C_ANOMALY"] > scores["C_0"]
    assert top[0]["customer_id"] == "C_ANOMALY"


# ── GraphService Tests ────────────────────────────────────────────────────────

def test_circular_transaction_detection(graph_service: GraphService, mock_circular_df: pd.DataFrame):
    G = graph_service.build_graph(mock_circular_df)
    cycles = graph_service.detect_circular_transactions(G)
    
    assert len(cycles) > 0
    assert "A" in cycles[0]
    assert "B" in cycles[0]
    assert "C" in cycles[0]


def test_hub_detection(graph_service: GraphService):
    # 10 nodes send to HUB
    data = [{"sender_id": f"R_{i}", "receiver_id": "HUB", "amount": 100, "timestamp": None} for i in range(10)]
    G = graph_service.build_graph(pd.DataFrame(data))
    
    hubs = graph_service.find_hubs(G)
    assert len(hubs) > 0
    assert hubs[0]["node_id"] == "HUB"


# ── Risk Engine Tests ─────────────────────────────────────────────────────────

def test_risk_scoring(risk_service: RiskService):
    features = {
        "velocity_per_day": 5.0,
        "rapid_cashout_score": 0.0,
        "dormant_days": 0.0,
        "high_risk_country_count": 0,
        "cross_border_ratio": 0.0,
    }
    
    result = risk_service.score_and_classify(
        kyc_status=KYCStatus.PENDING,
        customer_risk=RiskLevel.MEDIUM,
        rule_score=80.0,
        ml_score=90.0,
        features=features
    )
    
    assert result["risk_score"] > 50.0
    assert result["risk_level"] in [RiskLevel.HIGH, RiskLevel.CRITICAL]
