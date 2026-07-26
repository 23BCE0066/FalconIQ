"""
Tool Registry

Central registry for all FalconIQ tools. The Supervisor resolves tools
by name through this registry — never via hardcoded switch statements.

Design:
- Tools are registered at application startup via dependency injection.
- The Planner emits ToolName strings; the Supervisor calls registry.get(name).
- If a tool name is unknown, ToolException is raised before execution begins.
"""
from typing import Dict, List, Optional

from app.core.exceptions import ToolException
from app.interfaces.tools import BaseTool
from app.logging.logger import get_logger

logger = get_logger(__name__)


class ToolRegistry:
    """
    Dynamic registry of all available FalconIQ tools.

    Thread-safe for read operations (Python GIL). Mutations (register/unregister)
    should only occur during application startup — never during request handling.
    """

    def __init__(self) -> None:
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """
        Registers a tool instance under its canonical name.
        Raises ToolException if a tool with that name is already registered.
        """
        if tool.name in self._tools:
            raise ToolException(
                f"Tool '{tool.name}' is already registered. Use unregister() first."
            )
        self._tools[tool.name] = tool
        logger.info("tool_registered", tool_name=tool.name)

    def unregister(self, tool_name: str) -> None:
        """Removes a tool from the registry by name."""
        if tool_name not in self._tools:
            raise ToolException(f"Cannot unregister unknown tool '{tool_name}'.")
        del self._tools[tool_name]
        logger.info("tool_unregistered", tool_name=tool_name)

    def get(self, tool_name: str) -> BaseTool:
        """
        Resolves and returns a tool instance by name.
        Raises ToolException if the tool is not found.
        """
        tool = self._tools.get(tool_name)
        if tool is None:
            available = ", ".join(self._tools.keys()) or "none"
            raise ToolException(
                f"Tool '{tool_name}' not found in registry. Available tools: [{available}]"
            )
        return tool

    def exists(self, tool_name: str) -> bool:
        """Returns True if a tool with the given name is registered."""
        return tool_name in self._tools

    def list_tools(self) -> List[str]:
        """Returns the names of all registered tools in registration order."""
        return list(self._tools.keys())

    def get_descriptions(self) -> Dict[str, str]:
        """
        Returns a name → description mapping of all registered tools.
        Used by the Planner Agent to build its system prompt dynamically.
        """
        return {name: tool.description for name, tool in self._tools.items()}

    def __len__(self) -> int:
        return len(self._tools)

    def __repr__(self) -> str:
        return f"ToolRegistry(tools={self.list_tools()})"
