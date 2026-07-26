"""
Service: AlertService

Business logic for the compliance alert lifecycle. Handles creation,
status transitions, and dashboard metric aggregation.
"""
from typing import Dict, List

from app.constants import AlertStatus, DetectionType, RiskLevel
from app.core.exceptions import ValidationException
from app.database.models.alert import Alert, AlertActionRequest, AlertCreate
from app.interfaces.services import BaseService
from app.repository.alert import AlertRepository


class AlertService(BaseService):
    """Business logic for alert management and HITL workflow."""

    def __init__(self, repository: AlertRepository) -> None:
        self._repo = repository

    def get_alert(self, alert_id: str) -> Alert:
        """Retrieves an alert by ID. Raises ValidationException if not found."""
        alert = self._repo.get(alert_id)
        if not alert:
            raise ValidationException(f"Alert '{alert_id}' not found.")
        return alert

    def get_pending_alerts(self, *, skip: int = 0, limit: int = 100) -> List[Alert]:
        """Returns alerts awaiting review."""
        return self._repo.get_pending(skip=skip, limit=limit)

    def get_customer_alerts(self, customer_id: str) -> List[Alert]:
        """Returns all alerts for a specific customer."""
        return self._repo.get_by_customer(customer_id)

    def create_alert(self, payload: AlertCreate) -> Alert:
        """Creates a new compliance alert."""
        return self._repo.create(obj_in=payload)

    def apply_action(self, alert_id: str, action_req: AlertActionRequest) -> Alert:
        """
        Applies a HITL compliance officer action to an alert.
        Allows overturning previous decisions while preventing redundant re-actioning to the identical status.
        """
        alert = self.get_alert(alert_id)
        if alert.status == action_req.action and alert.status in (AlertStatus.APPROVED, AlertStatus.DISMISSED):
            raise ValidationException(
                f"Alert '{alert_id}' has already been actioned as '{alert.status.value}'."
            )
        return self._repo.apply_action(alert, action_req)

    def get_dashboard_metrics(self) -> Dict[str, int]:
        """Aggregates alert counts by status for the dashboard overview."""
        return {
            "total_pending": self._repo.count_by_status(AlertStatus.PENDING),
            "total_approved": self._repo.count_by_status(AlertStatus.APPROVED),
            "total_dismissed": self._repo.count_by_status(AlertStatus.DISMISSED),
            "total_under_review": self._repo.count_by_status(AlertStatus.UNDER_REVIEW),
            "total_escalated": self._repo.count_by_status(AlertStatus.ESCALATED),
        }
