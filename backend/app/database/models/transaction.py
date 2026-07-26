"""
SQLModel Domain Model: Transaction

Represents a single financial transaction between two bank accounts.
Indexed on sender, receiver, and timestamp for high-frequency AML queries.
"""
from datetime import datetime
from typing import Optional

from sqlmodel import Field, Index, SQLModel

from app.constants import TransactionType
from app.utils.id_generator import generate_transaction_id
from app.utils.time import utcnow


class TransactionBase(SQLModel):
    """Shared transaction fields used across models and schemas."""

    sender_id: str = Field(index=True, description="Customer ID of the transaction sender")
    receiver_id: str = Field(index=True, description="Customer ID of the transaction receiver")
    type: TransactionType = Field(description="Transaction category")
    amount: float = Field(gt=0, description="Transaction amount in the specified currency")
    currency: str = Field(default="USD", max_length=3, description="ISO 4217 currency code")
    country: str = Field(max_length=3, description="ISO 3166-1 alpha-3 country of transaction origin")
    timestamp: datetime = Field(description="Time the transaction was initiated")
    is_cross_border: bool = Field(default=False, description="Whether sender and receiver are in different countries")
    is_weekend: bool = Field(default=False, description="Whether transaction occurred on a weekend")
    is_night: bool = Field(default=False, description="Whether transaction occurred between 22:00 and 06:00 UTC")


class Transaction(TransactionBase, table=True):
    """
    Persisted transaction entity.

    Composite index on (sender_id, timestamp) accelerates velocity rule queries
    that look up all transactions by a customer within a rolling time window.
    """

    __tablename__ = "transactions"

    transaction_id: str = Field(
        default_factory=generate_transaction_id,
        primary_key=True,
        description="Unique transaction identifier (e.g. txn_abc123)"
    )
    created_at: datetime = Field(default_factory=utcnow)


class TransactionRead(TransactionBase):
    """Read schema returned by the API."""
    transaction_id: str
    created_at: datetime


class TransactionCreate(TransactionBase):
    """Write schema for creating a transaction record."""
    pass
