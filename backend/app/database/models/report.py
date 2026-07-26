"""
SQLModel Domain Model: ReportRecord

Persists user-generated investigations and compliance reports in Supabase / PostgreSQL.
Linked to the authenticated Clerk user ID so user reports remain available across logins.
"""
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel
from app.utils.time import utcnow
import uuid


def generate_report_id() -> str:
    """Generates a unique report ID."""
    return f"rpt_{uuid.uuid4().hex[:12]}"


class ReportRecord(SQLModel, table=True):
    """
    Persisted generated report record.
    """
    __tablename__ = "reports"  # type: ignore

    report_id: str = Field(
        default_factory=generate_report_id,
        primary_key=True,
        description="Unique report identifier"
    )
    user_id: str = Field(
        default="guest",
        index=True,
        description="Clerk user ID who created this report"
    )
    title: str = Field(description="Report title")
    type: str = Field(default="Suspicious Activity Report (SAR)", description="Report type")
    format: str = Field(default="markdown", description="Primary content structure")
    executive_summary: Optional[str] = Field(default="", description="Summary snippet of the report")
    full_markdown: str = Field(description="Complete report text used for dynamic PDF/DOC generation")
    status: str = Field(default="FINAL", description="Report lifecycle status")
    created_at: datetime = Field(
        default_factory=utcnow,
        description="Timestamp when report was generated"
    )
