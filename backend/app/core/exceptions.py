from enum import Enum

class ErrorCategory(str, Enum):
    DATA_ERROR = "DATA_ERROR"
    AI_ERROR = "AI_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    TOOL_ERROR = "TOOL_ERROR"
    SYSTEM_ERROR = "SYSTEM_ERROR"

class FalconIQException(Exception):
    """Base exception for all FalconIQ errors."""
    def __init__(self, message: str, category: ErrorCategory = ErrorCategory.SYSTEM_ERROR):
        self.message = message
        self.category = category
        super().__init__(f"[{category.value}] {self.message}")

class PlannerException(FalconIQException):
    """Raised when the Planner Agent fails to generate a valid plan."""
    def __init__(self, message: str):
        super().__init__(message, ErrorCategory.AI_ERROR)

class ToolException(FalconIQException):
    """Raised when a specific tool fails execution."""
    def __init__(self, message: str):
        super().__init__(message, ErrorCategory.TOOL_ERROR)

class RepositoryException(FalconIQException):
    """Raised when database operations fail."""
    def __init__(self, message: str):
        super().__init__(message, ErrorCategory.DATA_ERROR)

class LLMException(FalconIQException):
    """Raised when LLM API calls fail or timeout."""
    def __init__(self, message: str):
        super().__init__(message, ErrorCategory.AI_ERROR)

class ValidationException(FalconIQException):
    """Raised when data validation fails."""
    def __init__(self, message: str):
        super().__init__(message, ErrorCategory.VALIDATION_ERROR)

class DatasetException(FalconIQException):
    """Raised when dataset loading or transformation fails."""
    def __init__(self, message: str):
        super().__init__(message, ErrorCategory.DATA_ERROR)
