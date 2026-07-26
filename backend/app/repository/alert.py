"""
Repository: AlertRepository

Data access for compliance alerts. Exposes lifecycle queries used by the
Alert Management API and the Risk Engine's deduplication checks.
"""
from typing import List, Optional

from sqlmodel import Session, select

from app.constants import AlertStatus, RiskLevel
from app.core.exceptions import RepositoryException
from app.database.models.alert import Alert, AlertActionRequest, AlertCreate
from app.interfaces.repositories import BaseRepository
from app.utils.time import utcnow


class AlertRepository(BaseRepository[Alert, AlertCreate]):
    """Handles all database operations for the Alert entity."""

    model = Alert

    def __init__(self, session: Session) -> None:
        super().__init__(session)

    def get_by_customer(self, customer_id: str) -> List[Alert]:
        """Returns all alerts for a specific customer, newest first."""
        try:
            statement = (
                select(Alert)
                .where(Alert.customer_id == customer_id)
                .order_by(Alert.created_at.desc())  # type: ignore[attr-defined]
            )
            return list(self._session.exec(statement).all())
        except Exception as exc:
            raise RepositoryException(
                f"Failed to fetch alerts for customer '{customer_id}': {exc}"
            ) from exc

    def get_pending(self, *, skip: int = 0, limit: int = 100) -> List[Alert]:
        """Returns all alerts awaiting compliance officer review."""
        try:
            statement = (
                select(Alert)
                .where(Alert.status == AlertStatus.PENDING)
                .order_by(Alert.created_at.desc())  # type: ignore[attr-defined]
                .offset(skip)
                .limit(limit)
            )
            return list(self._session.exec(statement).all())
        except Exception as exc:
            raise RepositoryException(f"Failed to fetch pending alerts: {exc}") from exc

    def apply_action(self, alert: Alert, action_req: AlertActionRequest) -> Alert:
        """Applies a HITL compliance officer action to an alert."""
        updates = {
            "status": action_req.action,
            "officer_notes": action_req.notes,
            "reviewed_by": action_req.reviewed_by,
            "reviewed_at": utcnow(),
        }
        return self.update(db_obj=alert, updates=updates)

    def count_by_status(self, status: AlertStatus) -> int:
        """Returns the count of alerts in a given status for dashboard metrics."""
        try:
            from sqlmodel import func
            statement = (
                select(func.count())
                .select_from(Alert)
                .where(Alert.status == status)
            )
            return self._session.exec(statement).one() or 0
        except Exception as exc:
            raise RepositoryException(
                f"Failed to count alerts by status '{status}': {exc}"
            ) from exc
