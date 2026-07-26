from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.exceptions import FalconIQException
from app.logging.logger import get_logger

logger = get_logger(__name__)

async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catches all unhandled exceptions and returns a standardized JSON format."""
    
    if isinstance(exc, FalconIQException):
        logger.error(
            "business_exception_raised",
            error_type=exc.__class__.__name__,
            error_message=exc.message,
            path=request.url.path
        )
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error_type": exc.__class__.__name__,
                "message": exc.message
            }
        )
        
    logger.exception(
        "unhandled_exception_raised",
        error_type=exc.__class__.__name__,
        error_message=str(exc),
        path=request.url.path
    )
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error_type": "InternalServerError",
            "message": "An unexpected error occurred."
        }
    )
