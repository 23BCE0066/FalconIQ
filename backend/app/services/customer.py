"""
Service: CustomerService

Business logic for customer management. Orchestrates CustomerRepository
calls, applies domain rules, and raises domain-specific exceptions.
SQL never appears here — only business decisions.
"""
from typing import List, Optional

from app.constants import RiskLevel
from app.core.exceptions import ValidationException
from app.database.models.customer import Customer, CustomerCreate
from app.interfaces.services import BaseService
from app.repository.customer import CustomerRepository


class CustomerService(BaseService):
    """
    Business logic for customer operations.
    Injected with a CustomerRepository — never constructs one itself.
    """

    def __init__(self, repository: CustomerRepository) -> None:
        self._repo = repository

    def get_customer(self, customer_id: str) -> Customer:
        """
        Retrieves a customer by ID.
        Raises ValidationException if customer does not exist.
        """
        customer = self._repo.get(customer_id)
        if not customer:
            raise ValidationException(
                f"Customer '{customer_id}' not found."
            )
        return customer

    def create_customer(self, payload: CustomerCreate) -> Customer:
        """
        Creates a new customer after verifying email uniqueness.
        Raises ValidationException on duplicate email.
        """
        existing = self._repo.get_by_email(payload.email)
        if existing:
            raise ValidationException(
                f"A customer with email '{payload.email}' already exists."
            )
        return self._repo.create(obj_in=payload)

    def get_high_risk_customers(
        self, *, skip: int = 0, limit: int = 100
    ) -> List[Customer]:
        """Returns all HIGH and CRITICAL risk customers for dashboard display."""
        high = self._repo.get_by_risk_level(RiskLevel.HIGH, skip=skip, limit=limit)
        critical = self._repo.get_by_risk_level(RiskLevel.CRITICAL, skip=skip, limit=limit)
        return high + critical

    def update_risk_level(
        self, customer_id: str, new_risk: RiskLevel
    ) -> Customer:
        """Updates a customer's risk classification."""
        customer = self.get_customer(customer_id)
        return self._repo.update(
            db_obj=customer, updates={"risk_category": new_risk}
        )

    def get_risk_distribution(self) -> dict:
        """Returns a count of customers at each risk level for dashboard metrics."""
        return {
            level.value: self._repo.count_by_risk_level(level)
            for level in RiskLevel
        }
