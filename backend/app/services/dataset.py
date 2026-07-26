"""
Service: DatasetService

Responsible for all data loading operations. Applies filters, converts
ORM objects into pandas DataFrames, and provides caching helpers.

Business rule: data is loaded once per execution context. Tools never
touch SQLModel objects directly — they work with DataFrames from this service.
"""
from datetime import datetime, timedelta, timezone
from typing import List, Optional

import pandas as pd
from sqlmodel import Session

from app.constants import TransactionType
from app.core.exceptions import DatasetException
from app.database.models.customer import Customer
from app.database.models.transaction import Transaction
from app.interfaces.services import BaseService
from app.logging.logger import get_logger
from app.repository.customer import CustomerRepository
from app.repository.transaction import TransactionRepository

logger = get_logger(__name__)


class DatasetService(BaseService):
    """
    Loads, filters, and converts financial data to DataFrames.

    All AML tools consume DataFrames produced by this service — never raw ORM objects.
    Caching is the caller's responsibility (ExecutionContext.set_df).
    """

    # DataFrame cache keys used across tools
    DF_TRANSACTIONS = "transactions"
    DF_CUSTOMERS = "customers"

    def __init__(
        self,
        transaction_repo: TransactionRepository,
        customer_repo: CustomerRepository,
    ) -> None:
        self._tx_repo = transaction_repo
        self._cust_repo = customer_repo

    def load_transactions(
        self,
        *,
        days: Optional[int] = None,
        customer_id: Optional[str] = None,
        country: Optional[str] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        tx_type: Optional[TransactionType] = None,
        limit: int = 10_000,
    ) -> pd.DataFrame:
        """
        Loads transactions from the database and returns a typed DataFrame.

        Applies all provided filters in the database layer to minimise memory usage.
        Computed boolean columns (is_cross_border, is_weekend, is_night) are passed
        through from the stored model.

        Args:
            days: Rolling look-back window in days from now.
            customer_id: Filter to a specific sender.
            country: Filter to a specific country code.
            min_amount: Minimum transaction amount (inclusive).
            max_amount: Maximum transaction amount (inclusive).
            tx_type: Specific transaction type filter.
            limit: Maximum records to return (safety cap).

        Returns:
            DataFrame with columns matching the Transaction model.

        Raises:
            DatasetException: If the database query fails.
        """
        try:
            if customer_id:
                # Customer-scoped query: use windowed sender method
                if days:
                    now = datetime.now(timezone.utc)
                    from_dt = now - timedelta(days=days)
                    transactions = self._tx_repo.get_by_sender_in_window(
                        customer_id, from_dt, now
                    )
                else:
                    transactions = self._tx_repo.get_by_sender(customer_id, limit=limit)
            elif days:
                # Global windowed query
                now = datetime.now(timezone.utc)
                from_dt = now - timedelta(days=days)
                transactions = self._tx_repo.get_in_window(from_dt, now, limit=limit)
            else:
                transactions = self._tx_repo.get_multi(limit=limit)

            df = self._transactions_to_df(transactions)
            if df.empty:
                logger.warning("dataset_service_empty_result", customer_id=customer_id, days=days)
                return df

            # Apply in-memory filters that aren't handled at DB level
            if country:
                df = df[df["country"] == country]
            if min_amount is not None:
                df = df[df["amount"] >= min_amount]
            if max_amount is not None:
                df = df[df["amount"] <= max_amount]
            if tx_type:
                df = df[df["type"] == tx_type.value]

            logger.info(
                "dataset_loaded",
                rows=len(df),
                days=days,
                customer_id=customer_id,
                country=country,
            )
            return df

        except DatasetException:
            raise
        except Exception as exc:
            raise DatasetException(f"Failed to load transactions: {exc}") from exc

    def load_customers(self, *, limit: int = 5_000) -> pd.DataFrame:
        """
        Loads all customer records as a DataFrame.

        Returns:
            DataFrame with customer profile columns.
        """
        try:
            customers = self._cust_repo.get_multi(limit=limit)
            if not customers:
                return pd.DataFrame()
            records = [c.model_dump() for c in customers]
            return pd.DataFrame(records)
        except Exception as exc:
            raise DatasetException(f"Failed to load customers: {exc}") from exc

    def get_customer(self, customer_id: str) -> Optional[Customer]:
        """Retrieves a single customer ORM object."""
        return self._cust_repo.get(customer_id)

    @staticmethod
    def _transactions_to_df(transactions: List[Transaction]) -> pd.DataFrame:
        """Converts ORM Transaction objects to a typed DataFrame."""
        if not transactions:
            return pd.DataFrame()
        records = [t.model_dump() for t in transactions]
        df = pd.DataFrame(records)
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        df["amount"] = df["amount"].astype(float)
        # Ensure boolean columns exist even if missing from DB records
        for col in ("is_cross_border", "is_weekend", "is_night"):
            if col not in df.columns:
                df[col] = False
        return df
