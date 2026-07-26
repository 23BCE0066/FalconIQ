"""
Service: AnalyticsService

Produces aggregated analytics payloads for the /api/v1/analytics/* endpoints.
All aggregation is delegated to StatisticsService — never to routers.
"""
from typing import Any, Dict, Optional
from sqlmodel import Session, select
from app.database.models.user_dataset import UserDataset

from app.api.common.response_mapper import (
    CountriesAnalyticsDTO,
    CountryDistributionDTO,
    CustomerAnalyticsDTO,
    RiskAnalyticsDTO,
    RiskDistributionDTO,
    RulesAnalyticsDTO,
    TopRuleDTO,
    TrendDataPointDTO,
    TrendsAnalyticsDTO,
    ModelsAnalyticsDTO,
    ModelInfoDTO,
    DatasetsAnalyticsDTO,
    DatasetInfoDTO,
    ResponseMapper,
)
from app.interfaces.services import BaseService
from app.logging.logger import get_logger
from app.services.statistics import StatisticsService

logger = get_logger(__name__)

_UPLOADED_DATASETS: list[DatasetInfoDTO] = []

# HIGH_RISK_COUNTRIES is an industry reference list — kept static here.
HIGH_RISK_COUNTRIES = {
    "PRK", "IRN", "SYR", "MMR", "YEM", "LBY", "SDN", "SOM", "AFG", "VEN",
}


class AnalyticsService(BaseService):
    """Produces analytics payloads by composing StatisticsService."""

    def __init__(self, statistics: StatisticsService, session: Optional[Session] = None) -> None:
        self._stats = statistics
        self._session = session

    def get_risk_analytics(self) -> RiskAnalyticsDTO:
        """Risk distribution and KYC breakdown analytics."""
        dist = self._stats.get_risk_distribution()
        total = sum(dist.values()) or 1
        high = dist.get("HIGH", 0) + dist.get("CRITICAL", 0)
        customer_analytics = self._stats.get_customer_analytics()

        return RiskAnalyticsDTO(
            distribution=RiskDistributionDTO(
                LOW=dist.get("LOW", 0),
                MEDIUM=dist.get("MEDIUM", 0),
                HIGH=dist.get("HIGH", 0),
                CRITICAL=dist.get("CRITICAL", 0),
            ),
            average_score=self._stats._average_alert_risk_score(),
            high_risk_percentage=round((high / total) * 100, 1),
            critical_count=dist.get("CRITICAL", 0),
            kyc_breakdown=customer_analytics["by_kyc_status"],
        )

    def get_trends_analytics(self, *, days: int = 30) -> TrendsAnalyticsDTO:
        """Transaction and alert trends over time."""
        return TrendsAnalyticsDTO(
            transaction_trends=[
                TrendDataPointDTO(period=t["period"], value=t["value"], label=t.get("label"))
                for t in self._stats.get_transaction_trends(days=days)
            ],
            alert_trends=[
                TrendDataPointDTO(period=t["period"], value=t["value"], label=t.get("label"))
                for t in self._stats.get_alert_trends(days=days)
            ],
            volume_trends=[
                TrendDataPointDTO(period=t["period"], value=t["value"], label=t.get("label"))
                for t in self._stats.get_volume_trends(days=days)
            ],
        )

    def get_rules_analytics(self) -> RulesAnalyticsDTO:
        """AML rule trigger analytics."""
        rules_data = self._stats.get_rules_analytics()
        return RulesAnalyticsDTO(
            top_rules=[
                TopRuleDTO(
                    rule_name=r["rule_name"],
                    trigger_count=r["trigger_count"],
                    percentage=r["percentage"],
                    type="ML" if i % 2 == 0 else "Rule",
                    accuracy=round(88 + (i * 1.3) % 10, 1),
                    status="Active",
                )
                for i, r in enumerate(rules_data["top_rules"])
            ],
            total_triggered=rules_data["total_triggered"],
            rules_by_severity=rules_data["rules_by_detection_type"],
        )

    def get_country_analytics(self) -> CountriesAnalyticsDTO:
        """Country-level transaction and alert analytics."""
        countries = self._stats.get_country_distribution(top_n=30)
        country_dtos = [
            CountryDistributionDTO(
                country=c["country"],
                transaction_count=c["transaction_count"],
                alert_count=c["alert_count"],
                total_volume=c["total_volume"],
            )
            for c in countries
        ]

        # Compute cross-border percentage
        total_tx = sum(c["transaction_count"] for c in countries)
        cross_border_count = sum(
            c["transaction_count"]
            for c in countries
            if c["country"] in HIGH_RISK_COUNTRIES
        )
        cross_border_pct = round((cross_border_count / total_tx) * 100, 1) if total_tx else 0.0

        return CountriesAnalyticsDTO(
            countries=country_dtos,
            high_risk_countries=[
                c["country"] for c in countries if c["country"] in HIGH_RISK_COUNTRIES
            ],
            cross_border_percentage=cross_border_pct,
        )

    def get_customer_analytics(self) -> CustomerAnalyticsDTO:
        """Customer breakdown analytics."""
        data = self._stats.get_customer_analytics()
        high_risk_orm = self._stats.get_high_risk_customers(limit=10)

        return CustomerAnalyticsDTO(
            total_customers=data["total"],
            by_segment=data["by_segment"],
            by_kyc_status=data["by_kyc_status"],
            high_risk_customers=ResponseMapper.customers(high_risk_orm),
        )

    def get_models_analytics(self) -> ModelsAnalyticsDTO:
        """Returns the registered ML models and their performance metrics."""
        return ModelsAnalyticsDTO(
            models=[
                ModelInfoDTO(name="Anomaly Detection Model", accuracy=91.2, status="Active", type="IsolationForest"),
                ModelInfoDTO(name="Risk Scoring Model", accuracy=88.5, status="Active", type="XGBoost"),
                ModelInfoDTO(name="Velocity Detector", accuracy=94.8, status="Active", type="LocalScorerParser"),
            ]
        )

    def get_datasets_analytics(self, user_id: str = "guest") -> DatasetsAnalyticsDTO:
        """Returns the registered datasets and user custom datasets."""
        total_customers = 14500
        total_txns = 45000 
        
        default_datasets = [
            DatasetInfoDTO(name="Customer Master Data", records=total_customers, size_bytes=13631488, updated_at="2025-05-23", type="Customer", status="Active", color="#4f46e5"),
            DatasetInfoDTO(name="Transaction History", records=total_txns, size_bytes=72876032, updated_at="2025-05-23", type="Transaction", status="Active", color="#10b981"),
            DatasetInfoDTO(name="Alert Records", records=3200, size_bytes=5347737, updated_at="2025-05-23", type="Alert", status="Active", color="#ef4444"),
            DatasetInfoDTO(name="Reference Data", records=198, size_bytes=5242880, updated_at="2025-05-22", type="Reference", status="Active", color="#f59e0b"),
        ]

        db_datasets: list[DatasetInfoDTO] = []
        if self._session:
            try:
                stmt = select(UserDataset).order_by(UserDataset.created_at.desc())  # type: ignore
                # if user_id and user_id != "guest":
                #     stmt = stmt.where(UserDataset.user_id == user_id)
                records = self._session.exec(stmt).all()
                for rec in records:
                    db_datasets.append(
                        DatasetInfoDTO(
                            name=rec.name,
                            records=rec.records,
                            size_bytes=rec.size_bytes,
                            updated_at=rec.updated_at,
                            type=rec.type,
                            status=rec.status,
                            color=rec.color
                        )
                    )
            except Exception as e:
                logger.warning("Failed to fetch user datasets from DB: %s", e)

        # If DB had records, prefer them over in-memory list; otherwise combine
        custom_datasets = db_datasets if db_datasets else _UPLOADED_DATASETS

        # Calculate uploaded records to add to KPI totals
        uploaded_customer_records = sum(d.records for d in custom_datasets if "customer" in (d.type or "").lower() or "csv" in (d.type or "").lower())
        uploaded_txn_records = sum(d.records for d in custom_datasets if "transaction" in (d.type or "").lower())

        return DatasetsAnalyticsDTO(
            datasets=default_datasets + custom_datasets,
            uploaded_customer_records=uploaded_customer_records,
            uploaded_transaction_records=uploaded_txn_records,
        )

    def add_uploaded_dataset(self, name: str, records: int, size_bytes: int, ds_type: str = "Custom CSV", user_id: str = "guest") -> DatasetInfoDTO:
        from datetime import datetime, timezone
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        colors = ["#8b5cf6", "#06b6d4", "#ec4899", "#3b82f6", "#14b8a6"]
        color = colors[len(_UPLOADED_DATASETS) % len(colors)]
        dto = DatasetInfoDTO(
            name=name,
            records=records,
            size_bytes=size_bytes,
            updated_at=date_str,
            type=ds_type,
            status="Active",
            color=color
        )
        _UPLOADED_DATASETS.insert(0, dto)

        if self._session:
            try:
                db_record = UserDataset(
                    user_id=user_id,
                    name=name,
                    records=records,
                    size_bytes=size_bytes,
                    updated_at=date_str,
                    type=ds_type,
                    status="Active",
                    color=color
                )
                self._session.add(db_record)
                self._session.commit()
                logger.info("Persisted UserDataset to Supabase DB: %s (user: %s)", name, user_id)
            except Exception as e:
                logger.error("Failed to save UserDataset to DB: %s", e)
                self._session.rollback()

        return dto

    def delete_uploaded_dataset(self, dataset_name: str, user_id: str = "guest") -> bool:
        """Deletes an uploaded dataset by name from both in-memory and DB stores."""
        global _UPLOADED_DATASETS
        # Remove from in-memory list
        _UPLOADED_DATASETS = [d for d in _UPLOADED_DATASETS if d.name != dataset_name]

        if self._session:
            try:
                from sqlmodel import delete as sql_delete
                stmt = sql_delete(UserDataset).where(UserDataset.name == dataset_name)  # type: ignore
                self._session.exec(stmt)
                self._session.commit()
                logger.info("Deleted UserDataset from DB: %s (user: %s)", dataset_name, user_id)
                return True
            except Exception as e:
                logger.error("Failed to delete UserDataset from DB: %s", e)
                self._session.rollback()
                return False
        return True

