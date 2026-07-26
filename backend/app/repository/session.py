"""
Repository: SessionRepository

Persistence for agent execution sessions and their execution logs.
These records form the immutable audit trail of every AI investigation.
"""
from datetime import datetime
from typing import List, Optional

from sqlmodel import Session, select

from app.constants import SessionStatus
from app.core.exceptions import RepositoryException
from app.database.models.execution_log import AgentExecutionLog
from app.database.models.session import AgentSession
from app.utils.time import utcnow


class SessionRepository:
    """Handles all database operations for AgentSession and AgentExecutionLog."""

    def __init__(self, session: Session) -> None:
        self._session = session

    # ── AgentSession Methods ───────────────────────────────────────────────────

    def create_session(self, session_id: str, query: str) -> AgentSession:
        """Creates and persists a new agent session in RUNNING status."""
        try:
            obj = AgentSession(session_id=session_id, query=query)
            self._session.add(obj)
            self._session.commit()
            self._session.refresh(obj)
            return obj
        except Exception as exc:
            self._session.rollback()
            raise RepositoryException(f"Failed to create session: {exc}") from exc

    def get_session(self, session_id: str) -> Optional[AgentSession]:
        """Retrieves a session by its ID."""
        try:
            return self._session.get(AgentSession, session_id)
        except Exception as exc:
            raise RepositoryException(
                f"Failed to fetch session '{session_id}': {exc}"
            ) from exc

    def update_session(self, session_id: str, updates: dict) -> Optional[AgentSession]:
        """Applies partial updates to an existing session record."""
        obj = self.get_session(session_id)
        if not obj:
            return None
        try:
            for key, value in updates.items():
                if hasattr(obj, key):
                    setattr(obj, key, value)
            self._session.add(obj)
            self._session.commit()
            self._session.refresh(obj)
            return obj
        except Exception as exc:
            self._session.rollback()
            raise RepositoryException(
                f"Failed to update session '{session_id}': {exc}"
            ) from exc

    def mark_session_completed(
        self, session_id: str, total_time_ms: float
    ) -> Optional[AgentSession]:
        """Marks a session as COMPLETED with total wall-clock time."""
        return self.update_session(
            session_id,
            {
                "status": SessionStatus.COMPLETED,
                "completed_at": utcnow(),
                "total_execution_time_ms": total_time_ms,
            },
        )

    def mark_session_failed(
        self, session_id: str, error: str
    ) -> Optional[AgentSession]:
        """Marks a session as FAILED and stores the error log."""
        return self.update_session(
            session_id,
            {
                "status": SessionStatus.FAILED,
                "completed_at": utcnow(),
                "error_log": error,
            },
        )

    # ── AgentExecutionLog Methods ──────────────────────────────────────────────

    def log_tool_execution(
        self,
        session_id: str,
        tool_name: str,
        step_order: int,
        success: bool,
        execution_time_ms: float,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        duration_ms: Optional[float] = None,
        warnings: Optional[str] = None,
        summary: Optional[str] = None,
        confidence: Optional[float] = None,
        explanation: Optional[str] = None,
        input_payload: Optional[str] = None,
        output_payload: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> AgentExecutionLog:
        """Creates an immutable execution log entry for a single tool invocation."""
        try:
            log = AgentExecutionLog(
                session_id=session_id,
                tool_name=tool_name,
                step_order=step_order,
                success=success,
                execution_time_ms=execution_time_ms,
                start_time=start_time,
                end_time=end_time,
                duration_ms=duration_ms,
                warnings=warnings,
                summary=summary,
                confidence=confidence,
                explanation=explanation,
                input_payload=input_payload,
                output_payload=output_payload,
                error_message=error_message,
            )
            self._session.add(log)
            self._session.commit()
            self._session.refresh(log)
            return log
        except Exception as exc:
            self._session.rollback()
            raise RepositoryException(
                f"Failed to log tool execution for session '{session_id}': {exc}"
            ) from exc

    def get_logs_for_session(self, session_id: str) -> List[AgentExecutionLog]:
        """Returns all execution logs for a session, ordered by step."""
        try:
            statement = (
                select(AgentExecutionLog)
                .where(AgentExecutionLog.session_id == session_id)
                .order_by(AgentExecutionLog.step_order.asc())  # type: ignore[attr-defined]
            )
            return list(self._session.exec(statement).all())
        except Exception as exc:
            raise RepositoryException(
                f"Failed to fetch logs for session '{session_id}': {exc}"
            ) from exc
