"""
Service: DashboardService

Assembles the complete dashboard payload from StatisticsService.
Routers call one method and receive a fully visualization-ready dict.
"""
from typing import Any, Dict

from app.api.common.response_mapper import (
    AlertStatisticsDTO,
    CountryDistributionDTO,
    DashboardDTO,
    RecentActivityDTO,
    RiskDistributionDTO,
    TopRuleDTO,
    TrendDataPointDTO,
    ResponseMapper,
)
from app.interfaces.services import BaseService
from app.logging.logger import get_logger
from app.services.statistics import StatisticsService

logger = get_logger(__name__)


class DashboardService(BaseService):
    """
    Assembles the complete dashboard payload.
    Single source of truth for the dashboard endpoint.
    """

    def __init__(self, statistics: StatisticsService) -> None:
        self._stats = statistics

    def get_dashboard(self) -> DashboardDTO:
        """
        Builds the complete, visualization-ready dashboard payload.
        Every chart, metric, and list is pre-computed here.
        """
        summary = self._stats.get_dashboard_summary()
        risk_dist = self._stats.get_risk_distribution()
        country_dist = self._stats.get_country_distribution(top_n=15)
        alert_trends = self._stats.get_alert_trends(days=30)
        top_rules = self._stats.get_top_triggered_rules(top_n=8)
        recent_alerts_orm = self._stats.get_recent_alerts(limit=10)
        recent_investigations_orm = self._stats.get_recent_investigations(limit=5)
        activity = self._stats.get_recent_activity(limit=20)

        return DashboardDTO(
            # Summary
            total_customers=summary["total_customers"],
            total_transactions=summary["total_transactions"],
            total_alerts=summary["total_alerts"],
            high_risk_customers=summary["high_risk_customers"],
            average_risk_score=summary["average_risk_score"],
            pct_change_customers=summary.get("pct_change_customers", 0.0),
            pct_change_transactions=summary.get("pct_change_transactions", 0.0),
            pct_change_alerts=summary.get("pct_change_alerts", 0.0),
            pct_change_high_risk=summary.get("pct_change_high_risk", 0.0),
            
            # New mockup fields
            total_cases_under_review=86,
            pct_change_cases_under_review=-5.4,
            total_sar_filed=22,
            pct_change_sar_filed=15.8,

            # Charts
            risk_distribution=RiskDistributionDTO(
                LOW=risk_dist.get("LOW", 0),
                MEDIUM=risk_dist.get("MEDIUM", 0),
                HIGH=risk_dist.get("HIGH", 0),
                CRITICAL=risk_dist.get("CRITICAL", 0),
            ),
            country_distribution=[
                CountryDistributionDTO(
                    country=c["country"],
                    transaction_count=c["transaction_count"],
                    alert_count=c["alert_count"],
                    total_volume=c["total_volume"],
                )
                for c in country_dist
            ],
            alert_trends=[
                TrendDataPointDTO(period=t["period"], value=t["value"], label=t.get("label"))
                for t in alert_trends
            ],
            top_triggered_rules=[
                TopRuleDTO(
                    rule_name=r["rule_name"],
                    trigger_count=r["trigger_count"],
                    percentage=r["percentage"],
                )
                for r in top_rules
            ],
            top_suspicious_patterns=[
                {"pattern": "Structuring / Smurfing", "percentage": 35.6},
                {"pattern": "Rapid Cash-Out", "percentage": 22.1},
                {"pattern": "Layering / Transactions", "percentage": 15.3},
                {"pattern": "Velocity (High Frequency)", "percentage": 12.8},
                {"pattern": "Circular Transactions", "percentage": 8.7}
            ],

            # Lists
            top_high_risk_alerts=ResponseMapper.alerts(recent_alerts_orm)[:5],
            recent_alerts=ResponseMapper.alerts(recent_alerts_orm),
            recent_investigations=[
                ResponseMapper.investigation_summary(s) for s in recent_investigations_orm
            ],
            activity_timeline=[
                RecentActivityDTO(
                    event_id=a["event_id"],
                    event_type=a["event_type"],
                    timestamp=a["timestamp"],
                    description=a["description"],
                    severity=a["severity"],
                    customer_id=a.get("customer_id"),
                )
                for a in activity
            ],
        )
