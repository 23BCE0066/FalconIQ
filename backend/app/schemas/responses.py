from pydantic import BaseModel
from typing import Any, Dict, Optional

class ErrorResponse(BaseModel):
    success: bool = False
    error_type: str
    message: str
    details: Optional[Dict[str, Any]] = None

class SuccessResponse(BaseModel):
    success: bool = True
    data: Any
    message: Optional[str] = None
