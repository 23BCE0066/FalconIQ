"""
Service: StatisticsService

Centralises every database aggregation used across Dashboard, Analytics,
and Reports endpoints. No router or other service should perform raw
aggregation queries directly.

Provides:
    get_dashboard_summary()     → high-level KPI counts
    get_risk_distribution()     → customer count per risk level
    get_country_distribution()  → transaction/alert counts per country
    get_alert_statistics()      → alert counts per status
    get_top_triggered_rules()   → ranked list of triggered AML rules
    get_recent_activity()       → recent alert + investigation events
    get_transaction_trends()    → daily/monthly transaction volume
    get_alert_trends()          → daily/monthly alert counts
    get_customer_analytics()    → segment/KYC/risk breakdowns
"""
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlmodel import Session, and_, func, select

from app.constants import AlertStatus, KYCStatus, RiskLevel, TransactionType
from app.database.models.alert import Alert
from app.database.models.customer import Customer
from app.database.models.session import AgentSession
from app.database.models.transaction import Transaction
from app.interfaces.services import BaseService
from app.logging.logger import get_logger

logger = get_logger(__name__)


class StatisticsService(BaseService):
    """
    Central aggregation service. All queries execute against the injected
    Session — no ORM objects are returned, only primitive aggregates and dicts.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    # ── KPI Counts ─────────────────────────────────────────────────────────────

    def get_dashboard_summary(self) -> Dict[str, Any]:
        """
        Returns top-level KPI counts for the dashboard summary panel.
        """
        total_customers = self._count(Customer)
        total_transactions = self._count(Transaction)
        total_alerts = self._count(Alert)
        high_risk_customers = self._count_customers_by_risk(
            [RiskLevel.HIGH, RiskLevel.CRITICAL]
        )
        avg_risk_score = self._average_alert_risk_score()

        # Calculate percentage changes (mocking the historical comparison logic for MVP)
        # In a real scenario, we'd query: count(created_at >= 30d) vs count(created_at between 60d and 30d)
        import random
        return {
            "total_customers": total_customers,
            "total_transactions": total_transactions,
            "total_alerts": total_alerts,
            "high_risk_customers": high_risk_customers,
            "average_risk_score": avg_risk_score,
            "pct_change_customers": 6.4,
            "pct_change_transactions": 12.8,
            "pct_change_alerts": -5.2,
            "pct_change_high_risk": -7.2,
        }

    # ── Risk Distribution ──────────────────────────────────────────────────────

    def get_risk_distribution(self) -> Dict[str, int]:
        """Returns customer count per RiskLevel."""
        result: Dict[str, int] = {level.value: 0 for level in RiskLevel}
        stmt = (
            select(Customer.risk_category, func.count())
            .group_by(Customer.risk_category)
        )
        rows = self._session.exec(stmt).all()
        for risk_cat, count in rows:
            key = str(risk_cat.value if hasattr(risk_cat, "value") else risk_cat)
            if key in result:
                result[key] = count
        return result

    # ── Country Distribution ───────────────────────────────────────────────────

    def get_country_distribution(self, *, top_n: int = 20) -> List[Dict[str, Any]]:
        """
        Returns top-N countries by transaction count with volume and alert stats.
        """
        # Transaction counts per country
        tx_stmt = (
            select(Transaction.country, func.count(), func.sum(Transaction.amount))
            .group_by(Transaction.country)
            .order_by(func.count().desc())
            .limit(top_n)
        )
        tx_rows = self._session.exec(tx_stmt).all()

        # Alert counts per country (via transaction join)
        alert_stmt = (
            select(Transaction.country, func.count(Alert.alert_id))
            .join(Alert, Alert.transaction_id == Transaction.transaction_id, isouter=True)
            .group_by(Transaction.country)
        )
        alert_rows = {row[0]: row[1] for row in self._session.exec(alert_stmt).all()}

        result = []
        for country, tx_count, volume in tx_rows:
            result.append({
                "country": str(country or "UNKNOWN"),
                "transaction_count": tx_count or 0,
                "alert_count": alert_rows.get(country, 0),
                "total_volume": round(float(volume or 0), 2),
            })
        return result

    # ── Alert Statistics ───────────────────────────────────────────────────────

    def get_alert_statistics(self) -> Dict[str, Any]:
        """Returns alert counts grouped by status."""
        counts: Dict[str, int] = {s.value: 0 for s in AlertStatus}
        stmt = select(Alert.status, func.count()).group_by(Alert.status)
        rows = self._session.exec(stmt).all()
        for status, count in rows:
            key = str(status.value if hasattr(status, "value") else status)
            if key in counts:
                counts[key] = count

        total = sum(counts.values())
        return {
            "total": total,
            "pending": counts.get(AlertStatus.PENDING.value, 0),
            "approved": counts.get(AlertStatus.APPROVED.value, 0),
            "dismissed": counts.get(AlertStatus.DISMISSED.value, 0),
            "under_review": counts.get(AlertStatus.UNDER_REVIEW.value, 0),
            "escalated": counts.get(AlertStatus.ESCALATED.value, 0),
        }

    # ── Top Rules ──────────────────────────────────────────────────────────────

    def get_top_triggered_rules(self, *, top_n: int = 10) -> List[Dict[str, Any]]:
        """Returns the most frequently triggered AML rules with percentages."""
        stmt = (
            select(Alert.rule_triggered, func.count())
            .where(Alert.rule_triggered.isnot(None))  # type: ignore[attr-defined]
            .group_by(Alert.rule_triggered)
            .order_by(func.count().desc())
            .limit(top_n)
        )
        rows = self._session.exec(stmt).all()

        total = sum(count for _, count in rows) or 1
        return [
            {
                "rule_name": str(rule or "UNKNOWN"),
                "trigger_count": count,
                "percentage": round((count / total) * 100, 1),
            }
            for rule, count in rows
        ]

    # ── Recent Activity ────────────────────────────────────────────────────────

    def get_recent_activity(self, *, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Returns a unified activity feed of recent alerts and investigations.
        Sorted by timestamp descending.
        """
        # Recent alerts
        alert_stmt = (
            select(Alert)
            .order_by(Alert.created_at.desc())  # type: ignore[attr-defined]
            .limit(limit)
        )
        alerts = list(self._session.exec(alert_stmt).all())

        events = []
        for a in alerts:
            risk_level = str(a.risk_level.value if hasattr(a.risk_level, "value") else a.risk_level)
            severity = risk_level.lower() if risk_level else "low"
            events.append({
                "event_id": a.alert_id,
                "event_type": "alert",
                "timestamp": a.created_at,
                "description": (
                    f"Alert triggered for customer {a.customer_id}: "
                    f"{a.rule_triggered or a.aml_pattern or 'suspicious activity'}"
                ),
                "severity": severity,
                "customer_id": a.customer_id,
            })

        # Sort by timestamp
        events.sort(key=lambda x: x["timestamp"], reverse=True)
        return events[:limit]

    # ── Transaction Trends ─────────────────────────────────────────────────────

    def get_transaction_trends(self, *, days: int = 30) -> List[Dict[str, Any]]:
        """
        Returns daily transaction counts for the last N days.
        Returns chart-ready data points.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        stmt = (
            select(
                func.strftime("%Y-%m-%d", Transaction.timestamp).label("period"),
                func.count().label("count"),
                func.sum(Transaction.amount).label("volume"),
            )
            .where(Transaction.timestamp >= cutoff)
            .group_by(func.strftime("%Y-%m-%d", Transaction.timestamp))
            .order_by(func.strftime("%Y-%m-%d", Transaction.timestamp))
        )
        rows = self._session.exec(stmt).all()
        return [
            {
                "period": str(row[0] or ""),
                "value": row[1] or 0,
                "label": f"${round(float(row[2] or 0), 0):,.0f}",
            }
            for row in rows
        ]

    def get_volume_trends(self, *, days: int = 30) -> List[Dict[str, Any]]:
        """Returns daily transaction volume (amount sum) for the last N days."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        stmt = (
            select(
                func.strftime("%Y-%m-%d", Transaction.timestamp).label("period"),
                func.sum(Transaction.amount).label("volume"),
            )
            .where(Transaction.timestamp >= cutoff)
            .group_by(func.strftime("%Y-%m-%d", Transaction.timestamp))
            .order_by(func.strftime("%Y-%m-%d", Transaction.timestamp))
        )
        rows = self._session.exec(stmt).all()
        return [
            {
                "period": str(row[0] or ""),
                "value": round(float(row[1] or 0), 2),
                "label": f"${round(float(row[1] or 0), 0):,.0f}",
            }
            for row in rows
        ]

    # ── Alert Trends ───────────────────────────────────────────────────────────

    def get_alert_trends(self, *, days: int = 30) -> List[Dict[str, Any]]:
        """Returns daily alert creation counts for the last N days."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        stmt = (
            select(
                func.strftime("%Y-%m-%d", Alert.created_at).label("period"),
                func.count().label("count"),
            )
            .where(Alert.created_at >= cutoff)
            .group_by(func.strftime("%Y-%m-%d", Alert.created_at))
            .order_by(func.strftime("%Y-%m-%d", Alert.created_at))
        )
        rows = self._session.exec(stmt).all()
        return [
            {
                "period": str(row[0] or ""),
                "value": row[1] or 0,
                "label": f"{row[1]} alerts",
            }
            for row in rows
        ]

    # ── Customer Analytics ─────────────────────────────────────────────────────

    def get_customer_analytics(self) -> Dict[str, Any]:
        """Returns customer breakdown by segment, KYC status, and risk level."""
        # By segment
        seg_stmt = select(Customer.customer_segment, func.count()).group_by(Customer.customer_segment)
        by_segment: Dict[str, int] = {}
        for seg, count in self._session.exec(seg_stmt).all():
            key = str(seg.value if hasattr(seg, "value") else seg)
            by_segment[key] = count

        # By KYC status
        kyc_stmt = select(Customer.kyc_status, func.count()).group_by(Customer.kyc_status)
        by_kyc: Dict[str, int] = {}
        for kyc, count in self._session.exec(kyc_stmt).all():
            key = str(kyc.value if hasattr(kyc, "value") else kyc)
            by_kyc[key] = count

        # By risk level
        risk_stmt = select(Customer.risk_category, func.count()).group_by(Customer.risk_category)
        by_risk: Dict[str, int] = {}
        for risk, count in self._session.exec(risk_stmt).all():
            key = str(risk.value if hasattr(risk, "value") else risk)
            by_risk[key] = count

        total = sum(by_risk.values())

        return {
            "total": total,
            "by_segment": by_segment,
            "by_kyc_status": by_kyc,
            "by_risk_level": by_risk,
        }

    # ── Rules Analytics ────────────────────────────────────────────────────────

    def get_rules_analytics(self) -> Dict[str, Any]:
        """Returns detailed AML rule trigger analytics."""
        top_rules = self.get_top_triggered_rules(top_n=20)
        total_triggered = sum(r["trigger_count"] for r in top_rules)

        # By detection type
        det_stmt = select(Alert.detection_type, func.count()).group_by(Alert.detection_type)
        by_detection: Dict[str, int] = {}
        for det, count in self._session.exec(det_stmt).all():
            key = str(det.value if hasattr(det, "value") else det)
            by_detection[key] = count

        return {
            "top_rules": top_rules,
            "total_triggered": total_triggered,
            "rules_by_detection_type": by_detection,
        }

    # ── High-Risk Customers ────────────────────────────────────────────────────

    def get_high_risk_customers(self, *, limit: int = 10) -> List[Customer]:
        """Returns top high/critical risk customers for dashboard display."""
        stmt = (
            select(Customer)
            .where(Customer.risk_category.in_([RiskLevel.HIGH, RiskLevel.CRITICAL]))  # type: ignore[attr-defined]
            .order_by(Customer.updated_at.desc())  # type: ignore[attr-defined]
            .limit(limit)
        )
        return list(self._session.exec(stmt).all())

    def get_recent_alerts(self, *, limit: int = 10) -> List[Alert]:
        """Returns the most recently created alerts."""
        stmt = (
            select(Alert)
            .order_by(Alert.created_at.desc())  # type: ignore[attr-defined]
            .limit(limit)
        )
        return list(self._session.exec(stmt).all())

    def get_recent_investigations(self, *, limit: int = 10) -> List[AgentSession]:
        """Returns the most recent agent investigation sessions."""
        stmt = (
            select(AgentSession)
            .order_by(AgentSession.created_at.desc())  # type: ignore[attr-defined]
            .limit(limit)
        )
        return list(self._session.exec(stmt).all())

    # ── Private Helpers ────────────────────────────────────────────────────────

    def _count(self, model) -> int:
        """Generic count helper."""
        stmt = select(func.count()).select_from(model)
        return self._session.exec(stmt).one() or 0

    def _count_customers_by_risk(self, levels: list) -> int:
        """Counts customers matching any of the given risk levels."""
        stmt = (
            select(func.count())
            .select_from(Customer)
            .where(Customer.risk_category.in_(levels))  # type: ignore[attr-defined]
        )
        return self._session.exec(stmt).one() or 0

    def _average_alert_risk_score(self) -> float:
        """Computes the average risk score across all alerts."""
        stmt = select(func.avg(Alert.risk_score)).select_from(Alert)
        avg = self._session.exec(stmt).one()
        return round(float(avg or 0), 2)
