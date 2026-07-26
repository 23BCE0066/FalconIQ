"""
Repository: TransactionRepository

Data access layer for transaction entities. AML queries are inherently
time-windowed and sender-scoped — this repository exposes those query patterns
as typed methods rather than exposing raw SQL to the service layer.
"""
from datetime import datetime
from typing import List, Optional

from sqlmodel import Session, and_, select

from app.core.exceptions import RepositoryException
from app.database.models.transaction import Transaction, TransactionCreate
from app.interfaces.repositories import BaseRepository


class TransactionRepository(BaseRepository[Transaction, TransactionCreate]):
    """Handles all database operations for the Transaction entity."""

    model = Transaction

    def __init__(self, session: Session) -> None:
        super().__init__(session)

    def get_by_sender(
        self, sender_id: str, *, skip: int = 0, limit: int = 500
    ) -> List[Transaction]:
        """Returns all transactions initiated by a given sender customer ID."""
        try:
            statement = (
                select(Transaction)
                .where(Transaction.sender_id == sender_id)
                .order_by(Transaction.timestamp.desc())  # type: ignore[attr-defined]
                .offset(skip)
                .limit(limit)
            )
            return list(self._session.exec(statement).all())
        except Exception as exc:
            raise RepositoryException(
                f"Failed to fetch transactions for sender '{sender_id}': {exc}"
            ) from exc

    def get_by_sender_in_window(
        self, sender_id: str, from_dt: datetime, to_dt: datetime
    ) -> List[Transaction]:
        """Returns transactions by sender within a specific datetime window."""
        try:
            statement = (
                select(Transaction)
                .where(
                    and_(
                        Transaction.sender_id == sender_id,
                        Transaction.timestamp >= from_dt,
                        Transaction.timestamp <= to_dt,
                    )
                )
                .order_by(Transaction.timestamp.asc())  # type: ignore[attr-defined]
            )
            return list(self._session.exec(statement).all())
        except Exception as exc:
            raise RepositoryException(
                f"Failed to fetch windowed transactions for '{sender_id}': {exc}"
            ) from exc

    def get_in_window(
        self, from_dt: datetime, to_dt: datetime, *, limit: int = 10000
    ) -> List[Transaction]:
        """Returns all transactions within a datetime window (for global analysis)."""
        try:
            statement = (
                select(Transaction)
                .where(
                    and_(
                        Transaction.timestamp >= from_dt,
                        Transaction.timestamp <= to_dt,
                    )
                )
                .order_by(Transaction.timestamp.asc())  # type: ignore[attr-defined]
                .limit(limit)
            )
            return list(self._session.exec(statement).all())
        except Exception as exc:
            raise RepositoryException(
                f"Failed to fetch transactions in window: {exc}"
            ) from exc

    def count_by_sender_in_window(
        self, sender_id: str, from_dt: datetime, to_dt: datetime
    ) -> int:
        """Counts transactions by sender in a time window — used for velocity checks."""
        return len(self.get_by_sender_in_window(sender_id, from_dt, to_dt))
