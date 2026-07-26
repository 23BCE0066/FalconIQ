"""
Common: Exception Handlers

Registers FastAPI exception handlers that convert FalconIQ domain exceptions
and standard HTTP exceptions into the standard ErrorEnvelope format.

All error responses follow the same structure:
    {
        "success": false,
        "error": { "code": "...", "category": "...", "message": "..." },
        "metadata": { ... }
    }

Usage:
    from app.api.common.exceptions import register_exception_handlers
    register_exception_handlers(app)
"""
from datetime import datetime, timezone

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.core.exceptions import (
    DatasetException,
    FalconIQException,
    LLMException,
    PlannerException,
    RepositoryException,
    ToolException,
    ValidationException,
)
from app.logging.logger import get_logger

logger = get_logger(__name__)


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


def _error_body(
    request: Request,
    code: str,
    category: str,
    message: str,
) -> dict:
    return {
        "success": False,
        "error": {
            "code": code,
            "category": category,
            "message": message,
        },
        "metadata": {
            "request_id": request.headers.get("X-Request-ID", "unknown"),
            "timestamp": _ts(),
            "version": "v1",
        },
    }


def register_exception_handlers(app: FastAPI) -> None:
    """
    Registers all exception handlers on the FastAPI application.
    Call once in main.py after the app is created.
    """

    @app.exception_handler(ValidationException)
    async def validation_exception_handler(
        request: Request, exc: ValidationException
    ) -> JSONResponse:
        logger.warning(
            "validation_exception",
            message=exc.message,
            path=request.url.path,
        )
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=_error_body(
                request,
                code="VALIDATION_ERROR",
                category="VALIDATION_ERROR",
                message=exc.message,
            ),
        )

    @app.exception_handler(RepositoryException)
    async def repository_exception_handler(
        request: Request, exc: RepositoryException
    ) -> JSONResponse:
        logger.error(
            "repository_exception",
            message=exc.message,
            path=request.url.path,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_error_body(
                request,
                code="DATABASE_ERROR",
                category="DATA_ERROR",
                message="A database error occurred. Please try again.",
            ),
        )

    @app.exception_handler(DatasetException)
    async def dataset_exception_handler(
        request: Request, exc: DatasetException
    ) -> JSONResponse:
        logger.error(
            "dataset_exception",
            message=exc.message,
            path=request.url.path,
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_error_body(
                request,
                code="DATASET_ERROR",
                category="DATA_ERROR",
                message=exc.message,
            ),
        )

    @app.exception_handler(ToolException)
    async def tool_exception_handler(
        request: Request, exc: ToolException
    ) -> JSONResponse:
        logger.error(
            "tool_exception",
            message=exc.message,
            path=request.url.path,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_error_body(
                request,
                code="TOOL_ERROR",
                category="TOOL_ERROR",
                message="Tool execution failed. Please retry.",
            ),
        )

    @app.exception_handler(PlannerException)
    async def planner_exception_handler(
        request: Request, exc: PlannerException
    ) -> JSONResponse:
        logger.error(
            "planner_exception",
            message=exc.message,
            path=request.url.path,
        )
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=_error_body(
                request,
                code="AI_PLANNER_ERROR",
                category="AI_ERROR",
                message="AI planning service unavailable. Please retry.",
            ),
        )

    @app.exception_handler(LLMException)
    async def llm_exception_handler(
        request: Request, exc: LLMException
    ) -> JSONResponse:
        logger.error(
            "llm_exception",
            message=exc.message,
            path=request.url.path,
        )
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=_error_body(
                request,
                code="LLM_ERROR",
                category="AI_ERROR",
                message="AI service temporarily unavailable.",
            ),
        )

    @app.exception_handler(FalconIQException)
    async def falconiq_exception_handler(
        request: Request, exc: FalconIQException
    ) -> JSONResponse:
        logger.error(
            "falconiq_exception",
            error_type=exc.__class__.__name__,
            message=exc.message,
            path=request.url.path,
        )
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=_error_body(
                request,
                code=exc.category.value,
                category=exc.category.value,
                message=exc.message,
            ),
        )

    @app.exception_handler(RequestValidationError)
    async def request_validation_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        # Extract the first validation error message for a clean response
        errors = exc.errors()
        first = errors[0] if errors else {}
        field = " → ".join(str(loc) for loc in first.get("loc", []))
        msg = first.get("msg", "Invalid input.")
        human_msg = f"Invalid value for '{field}': {msg}" if field else msg

        logger.warning(
            "request_validation_error",
            errors=str(errors[:3]),  # Log up to 3 errors
            path=request.url.path,
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_error_body(
                request,
                code="INVALID_INPUT",
                category="VALIDATION_ERROR",
                message=human_msg,
            ),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.exception(
            "unhandled_exception",
            error_type=exc.__class__.__name__,
            error_message=str(exc),
            path=request.url.path,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_error_body(
                request,
                code="INTERNAL_ERROR",
                category="SYSTEM_ERROR",
                message="An unexpected error occurred. Please contact support.",
            ),
        )
