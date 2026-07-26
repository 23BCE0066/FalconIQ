"""
SQLModel Domain Model: UserDataset

Persists metadata for custom CSV datasets uploaded by users in Supabase / PostgreSQL.
Linked to Clerk user ID for personalized data exploration and AI model usage.
"""
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel
from app.utils.time import utcnow
import uuid


def generate_dataset_id() -> str:
    """Generates a unique dataset record ID."""
    return f"ds_{uuid.uuid4().hex[:12]}"


class UserDataset(SQLModel, table=True):
    """
    Persisted user custom dataset metadata record.
    """
    __tablename__ = "user_datasets"  # type: ignore

    dataset_id: str = Field(
        default_factory=generate_dataset_id,
        primary_key=True,
        description="Unique dataset identifier"
    )
    user_id: str = Field(
        default="guest",
        index=True,
        description="Clerk user ID who uploaded this dataset"
    )
    name: str = Field(description="Dataset file name")
    records: int = Field(default=0, description="Total row count in CSV")
    size_bytes: int = Field(default=0, description="File size in bytes")
    updated_at: str = Field(description="Formatted update date string (YYYY-MM-DD)")
    type: str = Field(default="Uploaded CSV", description="Dataset category")
    status: str = Field(default="Active", description="Operational state")
    color: str = Field(default="#8b5cf6", description="UI badge hex color")
    created_at: datetime = Field(
        default_factory=utcnow,
        description="Timestamp when dataset was uploaded"
    )
