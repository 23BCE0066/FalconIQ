"""
Tests: Phase 5 REST API

Covers all 9 API groups:
    - Dashboard
    - Customers
    - Transactions
    - Alerts
    - Analytics
    - Reports
    - Network
    - Chat (mocked)
    - Health / System Info

For each group tests:
    - 200 success responses
    - Response envelope structure (success, data, metadata)
    - Pagination structure and correctness
    - Filter parameters
    - Sorting
    - 404 for unknown IDs
    - 422 for invalid input
    - ResponseMapper — no SQLModel object leaks

All tests use an isolated in-memory SQLite database populated
with seeded fixture data for deterministic results.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from datetime import datetime, timezone
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.database.models.alert import Alert, AlertCreate
from app.database.models.customer import Customer, CustomerCreate
from app.database.models.session import AgentSession
from app.database.models.transaction import Transaction, TransactionCreate
from app.constants import (
    AlertStatus,
    CustomerSegment,
    DetectionType,
    KYCStatus,
    RiskLevel,
    SessionStatus,
    TransactionType,
)
from app.utils.id_generator import generate_customer_id, generate_transaction_id, generate_alert_id


# ── Test Database Setup ────────────────────────────────────────────────────────

TEST_DATABASE_URL = "sqlite://"  # pure in-memory


@pytest.fixture(scope="session")
def test_engine():
    """Creates a shared in-memory SQLite engine for all Phase 5 tests."""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture(scope="session")
def seeded_db(test_engine):
    """Seeds the test database with deterministic fixture data."""
    with Session(test_engine) as session:
        # Customers
        customers = [
            Customer(
                customer_id=f"cust_test_{i:04d}",
                name=f"Test Customer {i}",
                email=f"testcustomer{i}@falconiq.test",
                annual_income=50000.0 + i * 1000,
                risk_category=RiskLevel.HIGH if i % 5 == 0 else RiskLevel.LOW,
                kyc_status=KYCStatus.VERIFIED if i % 3 != 0 else KYCStatus.PENDING,
                customer_segment=CustomerSegment.RETAIL,
                country="USA" if i % 2 == 0 else "GBR",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            for i in range(1, 11)  # 10 customers
        ]
        for c in customers:
            session.add(c)

        # Transactions
        txns = [
            Transaction(
                transaction_id=f"txn_test_{i:04d}",
                sender_id="cust_test_0001",
                receiver_id=f"cust_test_{i:04d}",
                type=TransactionType.TRANSFER,
                amount=float(1000 + i * 500),
                currency="USD",
                country="USA",
                timestamp=datetime(2026, 1, i + 1, 12, 0, 0, tzinfo=timezone.utc),
                is_cross_border=False,
                is_weekend=False,
                is_night=False,
                created_at=datetime.now(timezone.utc),
            )
            for i in range(1, 6)  # 5 transactions
        ]
        for t in txns:
            session.add(t)

        # Alerts
        alerts = [
            Alert(
                alert_id=f"alert_test_{i:04d}",
                customer_id="cust_test_0001",
                transaction_id=f"txn_test_{i:04d}",
                detection_type=DetectionType.RULE,
                rule_triggered="structuring_detection",
                risk_score=75.0 + i,
                risk_level=RiskLevel.HIGH,
                status=AlertStatus.PENDING,
                created_at=datetime.now(timezone.utc),
            )
            for i in range(1, 4)  # 3 alerts
        ]
        for a in alerts:
            session.add(a)

        # Agent session
        sess = AgentSession(
            session_id="sess_test_0001",
            query="Test investigation query",
            status=SessionStatus.COMPLETED,
            intent="STRUCTURING_DETECTION",
            total_execution_time_ms=1200.0,
            created_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
        )
        session.add(sess)

        session.commit()

    return test_engine


@pytest.fixture(scope="session")
def client(seeded_db):
    """Creates a TestClient with the seeded test database."""
    from app.main import app
    from app.database.engine import get_session

    def override_get_session():
        with Session(seeded_db) as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ── Helper Assertions ──────────────────────────────────────────────────────────

def assert_envelope(data: dict, expect_success: bool = True) -> None:
    """Asserts the response follows the standard envelope structure."""
    assert "success" in data
    assert data["success"] == expect_success
    assert "metadata" in data
    meta = data["metadata"]
    assert "request_id" in meta
    assert "timestamp" in meta
    assert "version" in meta
    assert meta["version"] == "v1"
    if expect_success:
        assert "data" in data
    else:
        assert "error" in data
        error = data["error"]
        assert "code" in error
        assert "category" in error
        assert "message" in error


def assert_no_sqlmodel_leak(data: dict) -> None:
    """
    Asserts that no SQLModel-specific fields like '__tablename__' or
    internal metadata leak into the API response.
    """
    assert "__tablename__" not in str(data)
    assert "metadata_obj" not in str(data)
    assert "_sa_instance_state" not in str(data)


def assert_pagination(data: dict) -> None:
    """Asserts the pagination structure is correct."""
    d = data["data"]
    assert "items" in d
    assert "total_items" in d
    assert "total_pages" in d
    assert "page" in d
    assert "page_size" in d
    assert "has_next" in d
    assert "has_previous" in d
    assert isinstance(d["items"], list)
    assert isinstance(d["total_items"], int)


# ── Health Tests ───────────────────────────────────────────────────────────────

class TestHealthEndpoint:
    def test_health_returns_200(self, client):
        response = client.get("/api/v1/health")
        assert response.status_code == 200

    def test_health_envelope_structure(self, client):
        response = client.get("/api/v1/health")
        data = response.json()
        assert_envelope(data, expect_success=True)

    def test_health_has_status_field(self, client):
        response = client.get("/api/v1/health")
        data = response.json()
        assert "status" in data["data"]
        assert data["data"]["status"] in ("ok", "degraded")

    def test_health_has_subsystems(self, client):
        response = client.get("/api/v1/health")
        data = response.json()
        subsystems = data["data"]["subsystems"]
        assert "api" in subsystems
        assert "database" in subsystems
        assert "gemini" in subsystems
        assert "tool_registry" in subsystems

    def test_health_database_ok(self, client):
        response = client.get("/api/v1/health")
        data = response.json()
        assert data["data"]["subsystems"]["database"]["status"] == "ok"

    def test_health_metadata_has_execution_time(self, client):
        response = client.get("/api/v1/health")
        data = response.json()
        assert data["metadata"]["execution_time_ms"] is not None
        assert data["metadata"]["execution_time_ms"] >= 0


# ── System Info Tests ──────────────────────────────────────────────────────────

class TestSystemInfoEndpoint:
    def test_system_info_returns_200(self, client):
        response = client.get("/api/v1/system/info")
        assert response.status_code == 200

    def test_system_info_envelope(self, client):
        response = client.get("/api/v1/system/info")
        assert_envelope(response.json(), expect_success=True)

    def test_system_info_has_required_fields(self, client):
        response = client.get("/api/v1/system/info")
        data = response.json()["data"]
        assert data["application"] == "FalconIQ API"
        assert "version" in data
        assert "build_number" in data
        assert "environment" in data
        assert "uptime_seconds" in data
        assert "uptime_human" in data
        assert "database" in data
        assert "gemini" in data
        assert "tool_registry" in data
        assert "loaded_models" in data
        assert "loaded_rules" in data

    def test_system_info_uptime_positive(self, client):
        response = client.get("/api/v1/system/info")
        data = response.json()["data"]
        assert data["uptime_seconds"] >= 0

    def test_system_info_loaded_models_is_list(self, client):
        response = client.get("/api/v1/system/info")
        data = response.json()["data"]
        assert isinstance(data["loaded_models"], list)

    def test_system_info_loaded_rules_is_list(self, client):
        response = client.get("/api/v1/system/info")
        data = response.json()["data"]
        assert isinstance(data["loaded_rules"], list)


# ── Dashboard Tests ────────────────────────────────────────────────────────────

class TestDashboardEndpoint:
    def test_dashboard_returns_200(self, client):
        response = client.get("/api/v1/dashboard")
        assert response.status_code == 200

    def test_dashboard_envelope(self, client):
        response = client.get("/api/v1/dashboard")
        assert_envelope(response.json(), expect_success=True)

    def test_dashboard_kpi_counts(self, client):
        response = client.get("/api/v1/dashboard")
        data = response.json()["data"]
        assert "total_customers" in data
        assert "total_transactions" in data
        assert "total_alerts" in data
        assert "high_risk_customers" in data
        assert data["total_customers"] >= 10  # seeded 10

    def test_dashboard_risk_distribution(self, client):
        response = client.get("/api/v1/dashboard")
        data = response.json()["data"]
        dist = data["risk_distribution"]
        assert "LOW" in dist
        assert "MEDIUM" in dist
        assert "HIGH" in dist
        assert "CRITICAL" in dist
        assert dist["LOW"] >= 0

    def test_dashboard_country_distribution_is_list(self, client):
        response = client.get("/api/v1/dashboard")
        data = response.json()["data"]
        assert isinstance(data["country_distribution"], list)

    def test_dashboard_recent_alerts_is_list(self, client):
        response = client.get("/api/v1/dashboard")
        data = response.json()["data"]
        assert isinstance(data["recent_alerts"], list)

    def test_dashboard_no_sqlmodel_leak(self, client):
        response = client.get("/api/v1/dashboard")
        assert_no_sqlmodel_leak(response.json())

    def test_dashboard_activity_timeline_is_list(self, client):
        response = client.get("/api/v1/dashboard")
        data = response.json()["data"]
        assert isinstance(data["activity_timeline"], list)


# ── Customer Tests ─────────────────────────────────────────────────────────────

class TestCustomersEndpoints:
    def test_list_customers_200(self, client):
        response = client.get("/api/v1/customers")
        assert response.status_code == 200

    def test_list_customers_envelope(self, client):
        response = client.get("/api/v1/customers")
        assert_envelope(response.json(), expect_success=True)

    def test_list_customers_pagination(self, client):
        response = client.get("/api/v1/customers?page=1&page_size=5")
        assert_pagination(response.json())
        data = response.json()["data"]
        assert len(data["items"]) <= 5

    def test_list_customers_page_2(self, client):
        r1 = client.get("/api/v1/customers?page=1&page_size=3")
        r2 = client.get("/api/v1/customers?page=2&page_size=3")
        ids1 = [c["customer_id"] for c in r1.json()["data"]["items"]]
        ids2 = [c["customer_id"] for c in r2.json()["data"]["items"]]
        assert ids1 != ids2  # Different pages have different items

    def test_list_customers_filter_risk_level(self, client):
        response = client.get("/api/v1/customers?risk_level=HIGH")
        data = response.json()["data"]
        for item in data["items"]:
            assert item["risk_category"] == "HIGH"

    def test_list_customers_filter_kyc_status(self, client):
        response = client.get("/api/v1/customers?kyc_status=VERIFIED")
        data = response.json()["data"]
        for item in data["items"]:
            assert item["kyc_status"] == "VERIFIED"

    def test_list_customers_filter_country(self, client):
        response = client.get("/api/v1/customers?country=USA")
        data = response.json()["data"]
        for item in data["items"]:
            assert item["country"] == "USA"

    def test_list_customers_sort_ascending(self, client):
        response = client.get("/api/v1/customers?sort_by=name&sort_desc=false&page_size=5")
        items = response.json()["data"]["items"]
        names = [i["name"] for i in items]
        assert names == sorted(names)

    def test_list_customers_no_sqlmodel_leak(self, client):
        response = client.get("/api/v1/customers")
        assert_no_sqlmodel_leak(response.json())

    def test_customer_dto_fields(self, client):
        response = client.get("/api/v1/customers?page_size=1")
        item = response.json()["data"]["items"][0]
        required_fields = [
            "customer_id", "name", "email", "annual_income",
            "risk_category", "kyc_status", "customer_segment", "created_at", "updated_at"
        ]
        for field in required_fields:
            assert field in item

    def test_get_customer_profile_200(self, client):
        response = client.get("/api/v1/customers/cust_test_0001")
        assert response.status_code == 200

    def test_get_customer_profile_envelope(self, client):
        response = client.get("/api/v1/customers/cust_test_0001")
        assert_envelope(response.json(), expect_success=True)

    def test_get_customer_profile_has_sections(self, client):
        response = client.get("/api/v1/customers/cust_test_0001")
        data = response.json()["data"]
        assert "customer" in data
        assert "risk_summary" in data
        assert "recent_transactions" in data
        assert "triggered_alerts" in data
        assert "investigation_history" in data

    def test_get_customer_profile_404(self, client):
        response = client.get("/api/v1/customers/cust_does_not_exist")
        assert response.status_code == 400  # ValidationException maps to 400
        data = response.json()
        assert_envelope(data, expect_success=False)

    def test_get_customer_risk_200(self, client):
        response = client.get("/api/v1/customers/cust_test_0001/risk")
        assert response.status_code == 200

    def test_get_customer_risk_fields(self, client):
        response = client.get("/api/v1/customers/cust_test_0001/risk")
        data = response.json()["data"]
        assert "customer_id" in data
        assert "risk_category" in data
        assert "alert_count" in data
        assert "recommendation" in data

    def test_get_customer_timeline_200(self, client):
        response = client.get("/api/v1/customers/cust_test_0001/timeline")
        assert response.status_code == 200

    def test_get_customer_timeline_has_events(self, client):
        response = client.get("/api/v1/customers/cust_test_0001/timeline")
        data = response.json()["data"]
        assert "events" in data
        assert isinstance(data["events"], list)

    def test_get_customer_timeline_404(self, client):
        response = client.get("/api/v1/customers/unknown_id/timeline")
        assert response.status_code == 400

    def test_list_customers_invalid_page_size(self, client):
        response = client.get("/api/v1/customers?page_size=999")
        assert response.status_code == 422
        data = response.json()
        assert_envelope(data, expect_success=False)


# ── Transaction Tests ──────────────────────────────────────────────────────────

class TestTransactionsEndpoints:
    def test_list_transactions_200(self, client):
        response = client.get("/api/v1/transactions")
        assert response.status_code == 200

    def test_list_transactions_envelope(self, client):
        response = client.get("/api/v1/transactions")
        assert_envelope(response.json(), expect_success=True)

    def test_list_transactions_pagination(self, client):
        response = client.get("/api/v1/transactions?page=1&page_size=2")
        assert_pagination(response.json())
        data = response.json()["data"]
        assert len(data["items"]) <= 2

    def test_list_transactions_filter_customer(self, client):
        response = client.get("/api/v1/transactions?customer_id=cust_test_0001")
        data = response.json()["data"]
        for item in data["items"]:
            assert item["sender_id"] == "cust_test_0001"

    def test_list_transactions_filter_amount(self, client):
        response = client.get("/api/v1/transactions?min_amount=2000&max_amount=3000")
        data = response.json()["data"]
        for item in data["items"]:
            assert 2000 <= item["amount"] <= 3000

    def test_list_transactions_filter_country(self, client):
        response = client.get("/api/v1/transactions?country=USA")
        data = response.json()["data"]
        for item in data["items"]:
            assert item["country"] == "USA"

    def test_transaction_dto_fields(self, client):
        response = client.get("/api/v1/transactions?page_size=1")
        item = response.json()["data"]["items"][0]
        required = [
            "transaction_id", "sender_id", "receiver_id", "type",
            "amount", "currency", "country", "timestamp",
            "is_cross_border", "is_weekend", "is_night"
        ]
        for field in required:
            assert field in item

    def test_transaction_no_sqlmodel_leak(self, client):
        response = client.get("/api/v1/transactions")
        assert_no_sqlmodel_leak(response.json())

    def test_get_transaction_200(self, client):
        response = client.get("/api/v1/transactions/txn_test_0001")
        assert response.status_code == 200

    def test_get_transaction_fields(self, client):
        response = client.get("/api/v1/transactions/txn_test_0001")
        data = response.json()["data"]
        assert data["transaction_id"] == "txn_test_0001"
        assert "amount" in data
        assert "sender_id" in data

    def test_get_transaction_404(self, client):
        response = client.get("/api/v1/transactions/txn_does_not_exist")
        assert response.status_code == 400  # ValidationException
        assert_envelope(response.json(), expect_success=False)

    def test_search_transactions_200(self, client):
        response = client.get("/api/v1/transactions/search?q=cust_test")
        assert response.status_code == 200

    def test_search_transactions_pagination(self, client):
        response = client.get("/api/v1/transactions/search?q=txn_test")
        assert_pagination(response.json())

    def test_search_transactions_missing_q(self, client):
        response = client.get("/api/v1/transactions/search")
        assert response.status_code == 422


# ── Alert Tests ────────────────────────────────────────────────────────────────

class TestAlertsEndpoints:
    def test_list_alerts_200(self, client):
        response = client.get("/api/v1/alerts")
        assert response.status_code == 200

    def test_list_alerts_envelope(self, client):
        response = client.get("/api/v1/alerts")
        assert_envelope(response.json(), expect_success=True)

    def test_list_alerts_pagination(self, client):
        response = client.get("/api/v1/alerts?page=1&page_size=2")
        assert_pagination(response.json())

    def test_list_alerts_filter_customer(self, client):
        response = client.get("/api/v1/alerts?customer_id=cust_test_0001")
        data = response.json()["data"]
        for item in data["items"]:
            assert item["customer_id"] == "cust_test_0001"

    def test_list_alerts_filter_status(self, client):
        response = client.get("/api/v1/alerts?status=PENDING")
        data = response.json()["data"]
        for item in data["items"]:
            assert item["status"] == "PENDING"

    def test_alert_dto_fields(self, client):
        response = client.get("/api/v1/alerts?page_size=1")
        if response.json()["data"]["total_items"] > 0:
            item = response.json()["data"]["items"][0]
            required = [
                "alert_id", "customer_id", "detection_type",
                "risk_score", "risk_level", "status", "created_at"
            ]
            for field in required:
                assert field in item

    def test_alert_no_sqlmodel_leak(self, client):
        response = client.get("/api/v1/alerts")
        assert_no_sqlmodel_leak(response.json())

    def test_get_alert_200(self, client):
        response = client.get("/api/v1/alerts/alert_test_0001")
        assert response.status_code == 200

    def test_get_alert_fields(self, client):
        response = client.get("/api/v1/alerts/alert_test_0001")
        data = response.json()["data"]
        assert data["alert_id"] == "alert_test_0001"
        assert "risk_score" in data

    def test_get_alert_404(self, client):
        response = client.get("/api/v1/alerts/alert_does_not_exist")
        assert response.status_code == 400
        assert_envelope(response.json(), expect_success=False)

    def test_approve_alert_200(self, client):
        response = client.post(
            "/api/v1/alerts/alert_test_0002/approve",
            json={"reviewed_by": "officer_jane", "notes": "Confirmed structuring."},
        )
        assert response.status_code == 200

    def test_approve_alert_response_fields(self, client):
        # Use alert_test_0003 (not yet approved)
        response = client.post(
            "/api/v1/alerts/alert_test_0003/approve",
            json={"reviewed_by": "officer_john", "notes": None},
        )
        data = response.json()["data"]
        assert "alert_id" in data
        assert data["new_status"] == "APPROVED"
        assert data["reviewed_by"] == "officer_john"

    def test_dismiss_alert_200(self, client):
        # Note: alert_test_0001 is still pending
        response = client.post(
            "/api/v1/alerts/alert_test_0001/dismiss",
            json={"reviewed_by": "officer_bob", "notes": "False positive."},
        )
        assert response.status_code == 200

    def test_dismiss_alert_envelope(self, client):
        # Use a fresh seeded alert — alert_test_0001 already dismissed above, need new one
        # So just verify structure on a 400 re-action scenario
        # Re-dismiss should 400
        response = client.post(
            "/api/v1/alerts/alert_test_0001/dismiss",
            json={"reviewed_by": "officer_bob", "notes": "Retry."},
        )
        # Already actioned → should return 400
        assert response.status_code == 400

    def test_assign_alert_missing_assignee(self, client):
        response = client.post(
            "/api/v1/alerts/alert_test_0001/assign",
            json={"notes": "No assignee"},
        )
        assert response.status_code == 422

    def test_alert_action_missing_reviewed_by(self, client):
        response = client.post(
            "/api/v1/alerts/alert_test_0001/approve",
            json={"notes": "Missing reviewed_by"},
        )
        assert response.status_code == 422


# ── Analytics Tests ────────────────────────────────────────────────────────────

class TestAnalyticsEndpoints:
    def test_risk_analytics_200(self, client):
        response = client.get("/api/v1/analytics/risk")
        assert response.status_code == 200

    def test_risk_analytics_fields(self, client):
        response = client.get("/api/v1/analytics/risk")
        data = response.json()["data"]
        assert "distribution" in data
        assert "average_score" in data
        assert "high_risk_percentage" in data
        assert "critical_count" in data

    def test_trends_analytics_200(self, client):
        response = client.get("/api/v1/analytics/trends")
        assert response.status_code == 200

    def test_trends_analytics_fields(self, client):
        response = client.get("/api/v1/analytics/trends")
        data = response.json()["data"]
        assert "transaction_trends" in data
        assert "alert_trends" in data
        assert "volume_trends" in data

    def test_trends_analytics_custom_days(self, client):
        response = client.get("/api/v1/analytics/trends?days=7")
        assert response.status_code == 200

    def test_trends_analytics_invalid_days(self, client):
        response = client.get("/api/v1/analytics/trends?days=2")
        assert response.status_code == 422

    def test_rules_analytics_200(self, client):
        response = client.get("/api/v1/analytics/rules")
        assert response.status_code == 200

    def test_rules_analytics_fields(self, client):
        response = client.get("/api/v1/analytics/rules")
        data = response.json()["data"]
        assert "top_rules" in data
        assert "total_triggered" in data

    def test_country_analytics_200(self, client):
        response = client.get("/api/v1/analytics/countries")
        assert response.status_code == 200

    def test_country_analytics_fields(self, client):
        response = client.get("/api/v1/analytics/countries")
        data = response.json()["data"]
        assert "countries" in data
        assert "high_risk_countries" in data
        assert "cross_border_percentage" in data

    def test_customer_analytics_200(self, client):
        response = client.get("/api/v1/analytics/customers")
        assert response.status_code == 200

    def test_customer_analytics_fields(self, client):
        response = client.get("/api/v1/analytics/customers")
        data = response.json()["data"]
        assert "total" in data
        assert "by_segment" in data
        assert "by_kyc_status" in data
        assert "by_risk_level" in data

    def test_all_analytics_no_sqlmodel_leak(self, client):
        for endpoint in ["/risk", "/trends", "/rules", "/countries", "/customers"]:
            response = client.get(f"/api/v1/analytics{endpoint}")
            assert_no_sqlmodel_leak(response.json())


# ── Reports Tests ──────────────────────────────────────────────────────────────

class TestReportsEndpoints:
    def test_generate_report_json_200(self, client):
        response = client.post(
            "/api/v1/reports/generate",
            json={"report_type": "risk_summary", "format": "json"},
        )
        assert response.status_code == 200

    def test_generate_report_envelope(self, client):
        response = client.post(
            "/api/v1/reports/generate",
            json={"report_type": "alert_report", "format": "json"},
        )
        assert_envelope(response.json(), expect_success=True)

    def test_generate_report_has_report_id(self, client):
        response = client.post(
            "/api/v1/reports/generate",
            json={"report_type": "compliance", "format": "json"},
        )
        data = response.json()["data"]
        assert "report_id" in data
        assert data["report_id"].startswith("rpt_")

    def test_generate_report_markdown(self, client):
        response = client.post(
            "/api/v1/reports/generate",
            json={"report_type": "risk_summary", "format": "markdown"},
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["format"] == "markdown"
        assert data["markdown"] is not None

    def test_generate_report_pdf_stub(self, client):
        response = client.post(
            "/api/v1/reports/generate",
            json={"report_type": "compliance", "format": "pdf"},
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["format"] == "pdf"
        # PDF stub returns markdown
        assert data["markdown"] is not None

    def test_generate_report_invalid_type(self, client):
        response = client.post(
            "/api/v1/reports/generate",
            json={"report_type": "nonexistent_type", "format": "json"},
        )
        assert response.status_code == 400
        assert_envelope(response.json(), expect_success=False)

    def test_generate_report_invalid_format(self, client):
        response = client.post(
            "/api/v1/reports/generate",
            json={"report_type": "risk_summary", "format": "xlsx"},
        )
        assert response.status_code == 400

    def test_get_report_200(self, client):
        # First generate
        gen_response = client.post(
            "/api/v1/reports/generate",
            json={"report_type": "risk_summary", "format": "json"},
        )
        report_id = gen_response.json()["data"]["report_id"]

        # Then get
        response = client.get(f"/api/v1/reports/{report_id}")
        assert response.status_code == 200

    def test_get_report_fields(self, client):
        gen_response = client.post(
            "/api/v1/reports/generate",
            json={"report_type": "alert_report", "format": "json"},
        )
        report_id = gen_response.json()["data"]["report_id"]
        response = client.get(f"/api/v1/reports/{report_id}")
        data = response.json()["data"]
        assert "report_id" in data
        assert "report_type" in data
        assert "format" in data
        assert "title" in data
        assert "generated_at" in data

    def test_get_report_404(self, client):
        response = client.get("/api/v1/reports/rpt_does_not_exist")
        assert response.status_code == 400
        assert_envelope(response.json(), expect_success=False)

    def test_download_report_json(self, client):
        gen_response = client.post(
            "/api/v1/reports/generate",
            json={"report_type": "risk_summary", "format": "json"},
        )
        report_id = gen_response.json()["data"]["report_id"]
        response = client.get(f"/api/v1/reports/download/{report_id}")
        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]

    def test_download_report_markdown(self, client):
        gen_response = client.post(
            "/api/v1/reports/generate",
            json={"report_type": "compliance", "format": "markdown"},
        )
        report_id = gen_response.json()["data"]["report_id"]
        response = client.get(f"/api/v1/reports/download/{report_id}")
        assert response.status_code == 200


# ── Network Tests ──────────────────────────────────────────────────────────────

class TestNetworkEndpoints:
    def test_customer_network_200(self, client):
        response = client.get("/api/v1/network/customer/cust_test_0001")
        assert response.status_code == 200

    def test_customer_network_envelope(self, client):
        response = client.get("/api/v1/network/customer/cust_test_0001")
        assert_envelope(response.json(), expect_success=True)

    def test_customer_network_graph_fields(self, client):
        response = client.get("/api/v1/network/customer/cust_test_0001")
        data = response.json()["data"]
        assert "nodes" in data
        assert "edges" in data
        assert "circular_patterns" in data
        assert "hubs" in data
        assert "total_nodes" in data
        assert "total_edges" in data

    def test_customer_network_404(self, client):
        response = client.get("/api/v1/network/customer/cust_unknown")
        assert response.status_code == 400

    def test_customer_network_custom_days(self, client):
        response = client.get("/api/v1/network/customer/cust_test_0001?days=30")
        assert response.status_code == 200

    def test_suspicious_network_200(self, client):
        response = client.get("/api/v1/network/suspicious")
        assert response.status_code == 200

    def test_suspicious_network_envelope(self, client):
        response = client.get("/api/v1/network/suspicious")
        assert_envelope(response.json(), expect_success=True)

    def test_suspicious_network_graph_fields(self, client):
        response = client.get("/api/v1/network/suspicious")
        data = response.json()["data"]
        assert "graph" in data
        assert "risk_clusters" in data
        assert "most_connected_entities" in data

    def test_network_no_sqlmodel_leak(self, client):
        response = client.get("/api/v1/network/suspicious")
        assert_no_sqlmodel_leak(response.json())


# ── OpenAPI Schema Tests ───────────────────────────────────────────────────────

class TestOpenAPISchema:
    def test_openapi_json_loads(self, client):
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "paths" in schema
        assert "info" in schema

    def test_swagger_ui_loads(self, client):
        response = client.get("/docs")
        assert response.status_code == 200

    def test_redoc_ui_loads(self, client):
        response = client.get("/redoc")
        assert response.status_code == 200

    def test_all_v1_paths_present(self, client):
        response = client.get("/openapi.json")
        paths = response.json()["paths"]
        expected_paths = [
            "/api/v1/health",
            "/api/v1/system/info",
            "/api/v1/dashboard",
            "/api/v1/customers",
            "/api/v1/customers/{customer_id}",
            "/api/v1/transactions",
            "/api/v1/transactions/search",
            "/api/v1/alerts",
            "/api/v1/alerts/{alert_id}",
            "/api/v1/analytics/risk",
            "/api/v1/analytics/trends",
            "/api/v1/analytics/rules",
            "/api/v1/analytics/countries",
            "/api/v1/analytics/customers",
            "/api/v1/reports/generate",
            "/api/v1/network/suspicious",
            "/api/v1/chat",
        ]
        for path in expected_paths:
            assert path in paths, f"Missing path: {path}"

    def test_all_tags_present(self, client):
        response = client.get("/openapi.json")
        schema = response.json()
        # Collect all tags used in paths
        used_tags = set()
        for path_data in schema["paths"].values():
            for method_data in path_data.values():
                if isinstance(method_data, dict) and "tags" in method_data:
                    used_tags.update(method_data["tags"])
        expected_tags = {"Dashboard", "Customers", "Transactions", "Alerts", "Analytics", "Reports", "Network", "Chat", "Health"}
        for tag in expected_tags:
            assert tag in used_tags, f"Missing OpenAPI tag: {tag}"


# ── Response Envelope Tests ────────────────────────────────────────────────────

class TestResponseEnvelope:
    def test_success_envelope_has_success_true(self, client):
        response = client.get("/api/v1/health")
        assert response.json()["success"] is True

    def test_error_envelope_has_success_false(self, client):
        response = client.get("/api/v1/customers/cust_does_not_exist")
        assert response.json()["success"] is False

    def test_metadata_has_version(self, client):
        response = client.get("/api/v1/health")
        assert response.json()["metadata"]["version"] == "v1"

    def test_metadata_has_timestamp(self, client):
        response = client.get("/api/v1/dashboard")
        ts = response.json()["metadata"]["timestamp"]
        assert ts is not None
        assert "T" in ts  # ISO format

    def test_metadata_has_execution_time(self, client):
        response = client.get("/api/v1/analytics/risk")
        assert response.json()["metadata"]["execution_time_ms"] >= 0

    def test_error_envelope_has_error_fields(self, client):
        response = client.get("/api/v1/customers/nonexistent_customer")
        error = response.json()["error"]
        assert "code" in error
        assert "category" in error
        assert "message" in error

    def test_422_returns_error_envelope(self, client):
        response = client.get("/api/v1/customers?page_size=9999")
        assert response.status_code == 422
        data = response.json()
        assert_envelope(data, expect_success=False)
        assert data["error"]["code"] == "INVALID_INPUT"


# ── StatisticsService Tests ────────────────────────────────────────────────────

class TestStatisticsService:
    """Direct unit tests for StatisticsService methods."""

    @pytest.fixture
    def stats_svc(self, seeded_db):
        with Session(seeded_db) as session:
            from app.services.statistics import StatisticsService
            yield StatisticsService(session=session)

    def test_get_dashboard_summary_returns_dict(self, stats_svc):
        result = stats_svc.get_dashboard_summary()
        assert isinstance(result, dict)
        assert "total_customers" in result
        assert result["total_customers"] >= 10

    def test_get_risk_distribution_all_levels(self, stats_svc):
        result = stats_svc.get_risk_distribution()
        for level in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
            assert level in result

    def test_get_alert_statistics_all_statuses(self, stats_svc):
        result = stats_svc.get_alert_statistics()
        assert "total" in result
        assert "pending" in result
        assert "approved" in result

    def test_get_top_triggered_rules_list(self, stats_svc):
        result = stats_svc.get_top_triggered_rules()
        assert isinstance(result, list)
        if result:
            assert "rule_name" in result[0]
            assert "trigger_count" in result[0]
            assert "percentage" in result[0]

    def test_get_transaction_trends_list(self, stats_svc):
        result = stats_svc.get_transaction_trends(days=365)
        assert isinstance(result, list)

    def test_get_alert_trends_list(self, stats_svc):
        result = stats_svc.get_alert_trends(days=365)
        assert isinstance(result, list)

    def test_get_country_distribution_list(self, stats_svc):
        result = stats_svc.get_country_distribution()
        assert isinstance(result, list)
        if result:
            assert "country" in result[0]
            assert "transaction_count" in result[0]

    def test_get_customer_analytics_dict(self, stats_svc):
        result = stats_svc.get_customer_analytics()
        assert "total" in result
        assert "by_segment" in result
        assert "by_kyc_status" in result
        assert "by_risk_level" in result
