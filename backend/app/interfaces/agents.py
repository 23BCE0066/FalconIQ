"""
Base Class: BaseAgent

Abstract base for all agents (Planner, Supervisor). Enforces the `process()`
contract and provides structured logging at entry and exit.
"""
from abc import ABC, abstractmethod
from typing import Any

from app.logging.logger import get_logger

logger = get_logger(__name__)


class BaseAgent(ABC):
    """Abstract base class for FalconIQ agents."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable agent name for logging."""

    @abstractmethod
    async def process(self, *args: Any, **kwargs: Any) -> Any:
        """
        Core agent processing method.
        Concrete agents define their own typed signature.
        """
