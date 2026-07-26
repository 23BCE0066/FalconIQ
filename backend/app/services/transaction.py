"""
Service: TransactionService

Business logic for transaction management. Wraps TransactionRepository and
provides list/search/detail operations with filter support.

SQL never appears here — only business decisions and repository calls.
"""
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from sqlmodel import Session, and_, func, or_, select

from app.api.common.filters import TransactionFilters
from app.core.exceptions import ValidationException
from app.database.models.transaction import Transaction
from app.interfaces.services import BaseService
from app.logging.logger import get_logger
from app.repository.transaction import TransactionRepository

logger = get_logger(__name__)


class TransactionService(BaseService):
    """
    Business logic for transaction retrieval and search.
    Uses both the typed TransactionRepository and a raw Session for
    complex count queries that the base repository doesn't provide.
    """

    def __init__(
        self,
        repository: TransactionRepository,
        session: Session,
    ) -> None:
        self._repo = repository
        self._session = session

    def get_transaction(self, transaction_id: str) -> Transaction:
        """Retrieves a single transaction by ID."""
        tx = self._repo.get(transaction_id)
        if not tx:
            raise ValidationException(f"Transaction '{transaction_id}' not found.")
        return tx

    def list_transactions(
        self,
        filters: TransactionFilters,
        page: int = 1,
        page_size: int = 50,
    ) -> Tuple[List[Transaction], int]:
        """
        Returns a paginated, filtered list of transactions and the total count.
        Applies all active filters from the TransactionFilters dependency.
        """
        skip = (page - 1) * page_size

        # Build filter conditions
        conditions = self._build_conditions(filters)

        # Count query
        count_stmt = select(func.count()).select_from(Transaction)
        if conditions:
            count_stmt = count_stmt.where(and_(*conditions))
        total = self._session.exec(count_stmt).one() or 0

        # Data query
        stmt = select(Transaction)
        if conditions:
            stmt = stmt.where(and_(*conditions))

        # Sorting
        stmt = self._apply_sort(stmt, filters.sort_by, filters.sort_desc)
        stmt = stmt.offset(skip).limit(page_size)

        items = list(self._session.exec(stmt).all())
        return items, total

    def search_transactions(
        self,
        query: str,
        filters: Optional[TransactionFilters] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Tuple[List[Transaction], int]:
        """
        Searches transactions by sender_id, receiver_id, or transaction_id prefix.
        Optionally applies TransactionFilters on top.
        """
        skip = (page - 1) * page_size
        q = query.strip()

        search_conditions = [
            Transaction.transaction_id.startswith(q),   # type: ignore[attr-defined]
            Transaction.sender_id.startswith(q),         # type: ignore[attr-defined]
            Transaction.receiver_id.startswith(q),       # type: ignore[attr-defined]
        ]

        base_conditions = [or_(*search_conditions)]
        if filters:
            base_conditions.extend(self._build_conditions(filters))

        count_stmt = (
            select(func.count())
            .select_from(Transaction)
            .where(and_(*base_conditions))
        )
        total = self._session.exec(count_stmt).one() or 0

        sort_by = filters.sort_by if filters else "timestamp"
        sort_desc = filters.sort_desc if filters else True

        stmt = (
            select(Transaction)
            .where(and_(*base_conditions))
        )
        stmt = self._apply_sort(stmt, sort_by, sort_desc)
        stmt = stmt.offset(skip).limit(page_size)

        items = list(self._session.exec(stmt).all())
        return items, total

    def get_customer_transactions(
        self,
        customer_id: str,
        *,
        limit: int = 20,
    ) -> List[Transaction]:
        """Returns recent transactions for a customer (sent or received)."""
        stmt = (
            select(Transaction)
            .where(
                or_(
                    Transaction.sender_id == customer_id,
                    Transaction.receiver_id == customer_id,
                )
            )
            .order_by(Transaction.timestamp.desc())  # type: ignore[attr-defined]
            .limit(limit)
        )
        return list(self._session.exec(stmt).all())

    def count_total(self) -> int:
        """Returns total transaction count for dashboard metrics."""
        stmt = select(func.count()).select_from(Transaction)
        return self._session.exec(stmt).one() or 0

    # ── Private Helpers ────────────────────────────────────────────────────────

    def _build_conditions(self, filters: TransactionFilters) -> list:
        """Converts a TransactionFilters object into SQLModel WHERE conditions."""
        conditions = []

        if filters.customer_id:
            conditions.append(Transaction.sender_id == filters.customer_id)

        if filters.country:
            conditions.append(Transaction.country == filters.country)

        if filters.tx_type:
            conditions.append(Transaction.type == filters.tx_type)

        if filters.min_amount is not None:
            conditions.append(Transaction.amount >= filters.min_amount)

        if filters.max_amount is not None:
            conditions.append(Transaction.amount <= filters.max_amount)

        if filters.date_from:
            dt_from = datetime(
                filters.date_from.year,
                filters.date_from.month,
                filters.date_from.day,
                tzinfo=timezone.utc,
            )
            conditions.append(Transaction.timestamp >= dt_from)

        if filters.date_to:
            dt_to = datetime(
                filters.date_to.year,
                filters.date_to.month,
                filters.date_to.day,
                23, 59, 59,
                tzinfo=timezone.utc,
            )
            conditions.append(Transaction.timestamp <= dt_to)

        if filters.is_cross_border is not None:
            conditions.append(Transaction.is_cross_border == filters.is_cross_border)

        if filters.is_weekend is not None:
            conditions.append(Transaction.is_weekend == filters.is_weekend)

        return conditions

    def _apply_sort(self, stmt, sort_by: str, sort_desc: bool):
        """Applies ORDER BY clause to a select statement."""
        sort_map = {
            "timestamp": Transaction.timestamp,
            "amount": Transaction.amount,
            "country": Transaction.country,
            "created_at": Transaction.created_at,
        }
        col = sort_map.get(sort_by, Transaction.timestamp)
        if sort_desc:
            return stmt.order_by(col.desc())  # type: ignore[attr-defined]
        return stmt.order_by(col.asc())  # type: ignore[attr-defined]
