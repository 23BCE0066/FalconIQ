"""
Common: ResponseEnvelope

Defines the single, canonical response shape used by every endpoint in FalconIQ.
Routers never construct raw JSON — they call ctx.ok(data) or ctx.error(...).

Standard success response:
    {
        "success": true,
        "data": { ... },
        "metadata": {
            "request_id": "...",
            "execution_time_ms": 125,
            "timestamp": "...",
            "version": "v1"
        }
    }

Standard error response:
    {
        "success": false,
        "error": {
            "code": "NOT_FOUND",
            "category": "DATA_ERROR",
            "message": "Customer 'cust_x' not found."
        },
        "metadata": {
            "request_id": "...",
            "timestamp": "...",
            "version": "v1"
        }
    }
"""
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import Request
from pydantic import BaseModel


# ── DTO Shapes ─────────────────────────────────────────────────────────────────

class ResponseMetadata(BaseModel):
    """Metadata block attached to every response."""
    request_id: str
    execution_time_ms: Optional[float] = None
    timestamp: str
    version: str = "v1"


class ErrorDetail(BaseModel):
    """Structured error payload — never exposes internals."""
    code: str
    category: str
    message: str


class SuccessEnvelope(BaseModel):
    """Standard successful response envelope."""
    success: bool = True
    data: Any
    metadata: ResponseMetadata


class ErrorEnvelope(BaseModel):
    """Standard error response envelope."""
    success: bool = False
    error: ErrorDetail
    metadata: ResponseMetadata


# ── Request Context ────────────────────────────────────────────────────────────

class RequestContext:
    """
    Per-request context object.

    Captures request_id from headers (set by RequestIDMiddleware) and the
    precise start time of the request. Provides envelope-building helpers so
    that routers never manually construct response dictionaries.

    Usage (dependency injection):
        ctx: Annotated[RequestContext, Depends(get_request_context)]
        return ctx.ok(data)
    """

    def __init__(self, request_id: str, version: str = "v1", user_id: str = "guest") -> None:
        self.request_id = request_id
        self.version = version
        self.user_id = user_id
        self._start = time.perf_counter()

    def elapsed_ms(self) -> float:
        """Returns elapsed time in milliseconds since context creation."""
        return round((time.perf_counter() - self._start) * 1000, 2)

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _meta(self, *, include_timing: bool = True) -> ResponseMetadata:
        return ResponseMetadata(
            request_id=self.request_id,
            execution_time_ms=self.elapsed_ms() if include_timing else None,
            timestamp=self._now_iso(),
            version=self.version,
        )

    def ok(self, data: Any) -> Dict[str, Any]:
        """
        Wraps any data payload in the standard success envelope.
        Returns a plain dict to avoid double-serialisation with FastAPI.
        """
        envelope = SuccessEnvelope(data=data, metadata=self._meta())
        return envelope.model_dump()

    def error(
        self,
        *,
        code: str,
        category: str,
        message: str,
    ) -> Dict[str, Any]:
        """
        Builds a standard error envelope dict.
        Used by exception handlers only — routers raise HTTPException instead.
        """
        envelope = ErrorEnvelope(
            error=ErrorDetail(code=code, category=category, message=message),
            metadata=self._meta(include_timing=False),
        )
        return envelope.model_dump()


# ── FastAPI Dependency ─────────────────────────────────────────────────────────

def get_request_context(request: Request) -> RequestContext:
    """
    FastAPI dependency that creates a RequestContext for the current request.
    The request_id is read from the X-Request-ID header injected by
    RequestIDMiddleware. Falls back to a safe default if header is missing.
    Also extracts active user identity from Clerk authentication headers.
    """
    request_id = request.headers.get("X-Request-ID", "unknown")
    user_id = request.headers.get("X-Clerk-User-ID")
    if not user_id:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer ") and len(auth) > 20:
            # Use token signature fragment as stable user session identifier when explicit header is omitted
            user_id = f"clerk_user_{auth[10:22]}"
        else:
            user_id = "guest"
    return RequestContext(request_id=request_id, user_id=user_id)
