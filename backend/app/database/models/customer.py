"""
SQLModel Domain Model: Customer

Represents a bank customer entity. Acts as both the persistence model (SQLModel
table) and the schema that can be used directly in API responses.
"""
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel

from app.constants import CustomerSegment, KYCStatus, RiskLevel
from app.utils.id_generator import generate_customer_id
from app.utils.time import utcnow


class CustomerBase(SQLModel):
    """Shared fields used by both the DB model and creation schemas."""

    name: str = Field(min_length=1, max_length=255, description="Full legal name")
    email: str = Field(unique=True, index=True, description="Primary contact email")
    occupation: Optional[str] = Field(default=None, max_length=255)
    annual_income: float = Field(ge=0, description="Annual income in USD")
    risk_category: RiskLevel = Field(default=RiskLevel.LOW, description="Compliance risk tier")
    kyc_status: KYCStatus = Field(default=KYCStatus.PENDING, description="KYC verification status")
    customer_segment: CustomerSegment = Field(
        default=CustomerSegment.RETAIL, description="Bank customer segment"
    )
    country: Optional[str] = Field(default=None, max_length=3, description="ISO 3166-1 alpha-3 country code")


class Customer(CustomerBase, table=True):
    """
    Persisted customer entity.

    The `customer_id` is a prefixed UUID generated at creation time,
    providing human-readable tracing (e.g. 'cust_3f2a1b9c').
    """

    __tablename__ = "customers"

    customer_id: str = Field(
        default_factory=generate_customer_id,
        primary_key=True,
        description="Unique customer identifier (e.g. cust_abc123)"
    )
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class CustomerRead(CustomerBase):
    """Read schema returned by the API — includes generated fields."""
    customer_id: str
    created_at: datetime
    updated_at: datetime


class CustomerCreate(CustomerBase):
    """Write schema for creating a new customer."""
    pass
