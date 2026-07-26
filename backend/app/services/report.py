"""
Service: ReportService

Generates structured reports in JSON and Markdown formats.
PDF export is stubbed — returns Markdown with a note for future implementation.

Persists report metadata in memory for the application lifetime.
A persistent store can replace the in-memory dict in a future phase.
"""
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlmodel import Session, select
from app.database.models.report import ReportRecord

from pydantic import BaseModel

from app.api.common.response_mapper import ReportDTO, ResponseMapper
from app.interfaces.services import BaseService
from app.logging.logger import get_logger
from app.services.statistics import StatisticsService

logger = get_logger(__name__)


class ReportRequest(BaseModel):
    """Request body for report generation."""
    report_type: str  # "risk_summary", "transaction_analysis", "alert_report", "compliance"
    format: str = "json"  # "json", "markdown", "pdf"
    title: Optional[str] = None
    customer_id: Optional[str] = None
    days: int = 30


# In-memory report store — keyed by report_id
_REPORT_STORE: Dict[str, ReportDTO] = {}


class ReportService(BaseService):
    """
    Generates and retrieves compliance reports.
    Delegates all data aggregation to StatisticsService and persists to Supabase/SQLModel.
    """

    def __init__(self, statistics: StatisticsService, session: Optional[Session] = None) -> None:
        self._stats = statistics
        self._session = session

    def generate_report(self, request: ReportRequest, user_id: str = "guest") -> ReportDTO:
        """
        Generates a report of the requested type and format.
        Stores the result in DB (and memory cache) and returns its DTO.
        """
        report_id = f"rpt_{uuid.uuid4().hex[:12]}"
        title = request.title or self._default_title(request.report_type)
        generated_at = datetime.now(timezone.utc)

        # Build report content
        content, markdown = self._build_content(request)

        # Format selection
        fmt = request.format.lower()

        report = ReportDTO(
            report_id=report_id,
            report_type=request.report_type,
            format=fmt,
            title=title,
            generated_at=generated_at,
            status="completed",
            content=content if fmt == "json" else None,
            markdown=markdown if fmt in ("markdown", "pdf", "doc", "docx") else None,
            summary=self._build_summary(request.report_type, content),
        )

        _REPORT_STORE[report_id] = report

        if self._session:
            try:
                # Store full content representation in markdown string for flexible exports
                full_md = markdown or json.dumps(content or {}, indent=2, default=str)
                db_record = ReportRecord(
                    report_id=report_id,
                    user_id=user_id,
                    title=title,
                    type=request.report_type,
                    format=fmt,
                    executive_summary=report.summary,
                    full_markdown=full_md,
                    status="FINAL",
                    created_at=generated_at
                )
                self._session.add(db_record)
                self._session.commit()
                logger.info("Persisted ReportRecord to Supabase DB: %s (user: %s)", report_id, user_id)
            except Exception as e:
                logger.error("Failed to persist ReportRecord to DB: %s", e)
                self._session.rollback()

        logger.info(
            "report_generated",
            report_id=report_id,
            report_type=request.report_type,
            format=fmt,
        )
        return report

    def get_report(self, report_id: str) -> Optional[ReportDTO]:
        """Retrieves a previously generated report from DB or cache."""
        if report_id in _REPORT_STORE:
            return _REPORT_STORE[report_id]

        if self._session:
            try:
                rec = self._session.get(ReportRecord, report_id)
                if rec:
                    content_dict = None
                    md_str = rec.full_markdown
                    if rec.format == "json":
                        try:
                            content_dict = json.loads(rec.full_markdown)
                        except Exception:
                            content_dict = {"raw": rec.full_markdown}
                    dto = ReportDTO(
                        report_id=rec.report_id,
                        report_type=rec.type,
                        format=rec.format,
                        title=rec.title,
                        generated_at=rec.created_at,
                        status="completed",
                        content=content_dict,
                        markdown=md_str if rec.format != "json" else None,
                        summary=rec.executive_summary or "",
                    )
                    _REPORT_STORE[rec.report_id] = dto
                    return dto
            except Exception as e:
                logger.warning("Error fetching report %s from DB: %s", report_id, e)

        if not _REPORT_STORE:
            self.list_reports()
        return _REPORT_STORE.get(report_id)

    def list_reports(self, user_id: str = "guest") -> List[ReportDTO]:
        """Lists generated reports from Supabase DB and cache."""
        db_dtos: List[ReportDTO] = []
        if self._session:
            try:
                stmt = select(ReportRecord).order_by(ReportRecord.created_at.desc()) # type: ignore
                records = self._session.exec(stmt).all()
                for rec in records:
                    content_dict = None
                    md_str = rec.full_markdown
                    if rec.format == "json":
                        try:
                            content_dict = json.loads(rec.full_markdown)
                        except Exception:
                            content_dict = {"raw": rec.full_markdown}
                    dto = ReportDTO(
                        report_id=rec.report_id,
                        report_type=rec.type,
                        format=rec.format,
                        title=rec.title,
                        generated_at=rec.created_at,
                        status="completed",
                        content=content_dict,
                        markdown=md_str if rec.format != "json" else None,
                        summary=rec.executive_summary or "",
                    )
                    _REPORT_STORE[rec.report_id] = dto
                    db_dtos.append(dto)
                if db_dtos:
                    return db_dtos
            except Exception as e:
                logger.warning("Error listing reports from DB: %s", e)

        if not _REPORT_STORE:
            try:
                self.generate_report(ReportRequest(report_type="risk_summary", format="markdown", title="Q3 Comprehensive Risk Summary"))
                self.generate_report(ReportRequest(report_type="alert_report", format="json", title="Automated High-Risk Alert Analysis"))
                self.generate_report(ReportRequest(report_type="compliance", format="markdown", title="Executive AML Compliance Audit Report"))
                self.generate_report(ReportRequest(report_type="transaction_analysis", format="json", title="Monthly Cross-Border Transaction Velocity"))
            except Exception as e:
                logger.warning("Failed to preload initial reports: %s", e)
        return sorted(list(_REPORT_STORE.values()), key=lambda r: r.generated_at, reverse=True)

    def download_report(self, report_id: str) -> Optional[ReportDTO]:
        """Alias for get_report — used by the download endpoint."""
        return self.get_report(report_id)


    # ── Private Builders ───────────────────────────────────────────────────────

    def _build_content(self, request: ReportRequest):
        """Builds report content dict and Markdown string."""
        rtype = request.report_type

        if rtype == "risk_summary":
            data = self._build_risk_summary()
        elif rtype == "alert_report":
            data = self._build_alert_report()
        elif rtype == "transaction_analysis":
            data = self._build_transaction_analysis(days=request.days)
        elif rtype == "compliance":
            data = self._build_compliance_report()
        else:
            data = self._build_risk_summary()  # default

        markdown = self._to_markdown(request.report_type, data)
        return data, markdown

    def _build_risk_summary(self) -> Dict[str, Any]:
        summary = self._stats.get_dashboard_summary()
        risk_dist = self._stats.get_risk_distribution()
        high_risk = self._stats.get_high_risk_customers(limit=10)
        top_rules = self._stats.get_top_triggered_rules(top_n=10)
        return {
            "summary": summary,
            "risk_distribution": risk_dist,
            "high_risk_customers": [c.customer_id for c in high_risk],
            "top_triggered_rules": top_rules,
        }

    def _build_alert_report(self) -> Dict[str, Any]:
        alert_stats = self._stats.get_alert_statistics()
        top_rules = self._stats.get_top_triggered_rules(top_n=15)
        recent = self._stats.get_recent_alerts(limit=20)
        return {
            "alert_statistics": alert_stats,
            "top_triggered_rules": top_rules,
            "recent_alerts": [a.alert_id for a in recent],
            "total_alerts": alert_stats["total"],
        }

    def _build_transaction_analysis(self, days: int = 30) -> Dict[str, Any]:
        summary = self._stats.get_dashboard_summary()
        trends = self._stats.get_transaction_trends(days=days)
        country_dist = self._stats.get_country_distribution(top_n=10)
        return {
            "total_transactions": summary["total_transactions"],
            "period_days": days,
            "daily_trends": trends,
            "country_distribution": country_dist,
        }

    def _build_compliance_report(self) -> Dict[str, Any]:
        summary = self._stats.get_dashboard_summary()
        alert_stats = self._stats.get_alert_statistics()
        risk_dist = self._stats.get_risk_distribution()
        rules = self._stats.get_rules_analytics()
        return {
            "executive_summary": summary,
            "alert_statistics": alert_stats,
            "risk_distribution": risk_dist,
            "rule_analytics": rules,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    def _to_markdown(self, report_type: str, data: Dict[str, Any]) -> str:
        """Converts report data to a readable Markdown document."""
        title = self._default_title(report_type)
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        lines = [
            f"# {title}",
            f"**Generated:** {ts}  ",
            f"**Report Type:** `{report_type}`",
            "",
            "---",
            "",
        ]
        lines.append("## Data")
        lines.append("```json")
        lines.append(json.dumps(data, indent=2, default=str))
        lines.append("```")
        return "\n".join(lines)

    def _build_summary(self, report_type: str, data: Dict[str, Any]) -> str:
        summary = data.get("summary", {})
        if report_type == "risk_summary":
            dist = data.get("risk_distribution", {})
            return (
                f"Risk summary: {dist.get('CRITICAL', 0)} CRITICAL, "
                f"{dist.get('HIGH', 0)} HIGH risk customers. "
                f"Total alerts: {summary.get('total_alerts', 0)}."
            )
        elif report_type == "alert_report":
            stats = data.get("alert_statistics", {})
            return f"Alert report: {stats.get('total', 0)} total alerts, {stats.get('pending', 0)} pending review."
        elif report_type == "transaction_analysis":
            return (
                f"Transaction analysis for last {data.get('period_days', 30)} days: "
                f"{data.get('total_transactions', 0)} transactions."
            )
        return "FalconIQ compliance report generated successfully."

    def _default_title(self, report_type: str) -> str:
        titles = {
            "risk_summary": "FalconIQ Risk Summary Report",
            "alert_report": "FalconIQ Alert Analysis Report",
            "transaction_analysis": "FalconIQ Transaction Analysis Report",
            "compliance": "FalconIQ Compliance Overview Report",
        }
        return titles.get(report_type, "FalconIQ Report")
