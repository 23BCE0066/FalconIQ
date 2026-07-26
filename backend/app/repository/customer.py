"""
Repository: CustomerRepository

Data access layer for customer entities. Contains only database operations —
no business logic. Business rules live in CustomerService.
"""
from typing import List, Optional

from sqlmodel import Session, select

from app.constants import RiskLevel
from app.core.exceptions import RepositoryException
from app.database.models.customer import Customer, CustomerCreate
from app.interfaces.repositories import BaseRepository


class CustomerRepository(BaseRepository[Customer, CustomerCreate]):
    """Handles all database operations for the Customer entity."""

    model = Customer

    def __init__(self, session: Session) -> None:
        super().__init__(session)

    def get_by_email(self, email: str) -> Optional[Customer]:
        """Fetches a customer by their unique email address."""
        try:
            statement = select(Customer).where(Customer.email == email)
            return self._session.exec(statement).first()
        except Exception as exc:
            raise RepositoryException(f"Failed to fetch customer by email '{email}': {exc}") from exc

    def get_by_risk_level(
        self, risk_level: RiskLevel, *, skip: int = 0, limit: int = 100
    ) -> List[Customer]:
        """Returns all customers matching a specific risk level, paginated."""
        try:
            statement = (
                select(Customer)
                .where(Customer.risk_category == risk_level)
                .offset(skip)
                .limit(limit)
            )
            return list(self._session.exec(statement).all())
        except Exception as exc:
            raise RepositoryException(
                f"Failed to fetch customers by risk level '{risk_level}': {exc}"
            ) from exc

    def count_by_risk_level(self, risk_level: RiskLevel) -> int:
        """Returns a count of customers at the given risk level."""
        try:
            from sqlmodel import func
            statement = (
                select(func.count())
                .select_from(Customer)
                .where(Customer.risk_category == risk_level)
            )
            result = self._session.exec(statement).one()
            return result or 0
        except Exception as exc:
            raise RepositoryException(
                f"Failed to count customers by risk level: {exc}"
            ) from exc
