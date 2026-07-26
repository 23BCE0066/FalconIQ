"""
Base Class: BaseTool

Abstract base that every FalconIQ tool must extend. Enforces the standard
execute() contract and provides built-in timing so each tool automatically
reports its own execution_time_ms without boilerplate.

Extending tools must implement:
- name (property): canonical ToolName value
- description (property): human-readable capability description for Planner
- _run(context): core business logic — never called directly by Supervisor

Usage:
    class DatasetTool(BaseTool):
        @property
        def name(self) -> str:
            return ToolName.DATASET

        @property
        def description(self) -> str:
            return "Loads and filters transaction data from the database."

        async def _run(self, context: ExecutionContext) -> ToolResult:
            ...
"""
import time
from abc import ABC, abstractmethod

from app.logging.logger import get_logger
from app.schemas.execution_context import ExecutionContext
from app.schemas.tool_result import ToolResult

logger = get_logger(__name__)


class BaseTool(ABC):
    """
    Abstract base class for all FalconIQ tools.

    The `execute()` method handles timing instrumentation and top-level
    exception catching so individual tools only need to implement `_run()`.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Canonical tool name — must match a ToolName enum value."""

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description used by the Planner's system prompt."""

    @abstractmethod
    async def _run(self, context: ExecutionContext) -> ToolResult:
        """
        Core execution logic. Receives the shared context and returns a ToolResult.
        Guaranteed to be called with a valid, initialized context.
        """

    async def execute(self, context: ExecutionContext) -> ToolResult:
        """
        Public execution entry-point called by the Supervisor.

        Wraps `_run()` with:
        - Automatic wall-clock timing
        - Top-level exception handling → ToolResult.failure()
        - Structured logging of entry and exit
        """
        logger.info("tool_started", tool=self.name)
        start = time.perf_counter()

        try:
            result = await self._run(context)
            # Ensure timing is accurate even if the tool set its own
            if result.execution_time_ms == 0.0:
                result = result.model_copy(
                    update={
                        "execution_time_ms": round((time.perf_counter() - start) * 1000, 3),
                        "request_id": context.request_id,
                    }
                )
            else:
                result = result.model_copy(update={"request_id": context.request_id})

            logger.info(
                "tool_completed",
                tool=self.name,
                success=result.success,
                execution_time_ms=result.execution_time_ms,
            )
            return result

        except Exception as exc:
            elapsed = round((time.perf_counter() - start) * 1000, 3)
            logger.exception(
                "tool_failed",
                tool=self.name,
                error=str(exc),
            )
            return ToolResult.failure(
                tool_name=self.name,
                error=str(exc),
                execution_time_ms=elapsed,
            ).model_copy(update={"request_id": context.request_id})
