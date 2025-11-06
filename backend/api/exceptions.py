"""
Centralized exception handlers for the FastAPI application.
Ensures consistent error response format across all endpoints.
"""
import logging
import asyncio
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException
from pydantic import ValidationError

from backend.models.responses import ErrorResponse, ErrorDetail


logger = logging.getLogger(__name__)


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """
    Handle Pydantic validation errors (400 Bad Request).
    
    Triggered when request data fails Pydantic validation.
    Returns detailed validation error messages to help clients fix their requests.
    
    Args:
        request: The incoming request
        exc: The validation exception
        
    Returns:
        JSONResponse with 400 status and detailed validation errors
    """
    # Extract validation error details
    errors = exc.errors()
    
    # Build user-friendly error message
    if len(errors) == 1:
        error = errors[0]
        field = " -> ".join(str(loc) for loc in error["loc"] if loc != "body")
        message = f"Validation error in field '{field}': {error['msg']}"
    else:
        error_messages = []
        for error in errors:
            field = " -> ".join(str(loc) for loc in error["loc"] if loc != "body")
            error_messages.append(f"{field}: {error['msg']}")
        message = "Validation errors: " + "; ".join(error_messages)
    
    # Log the validation error
    logger.warning(
        f"Validation error for {request.method} {request.url.path}: {message}",
        extra={"errors": errors}
    )
    
    # Create error response
    error_response = ErrorResponse(
        error=ErrorDetail(
            code=status.HTTP_400_BAD_REQUEST,
            message=message
        )
    )
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=error_response.model_dump()
    )


async def http_exception_handler(
    request: Request,
    exc: HTTPException
) -> JSONResponse:
    """
    Handle HTTP exceptions (404, 403, etc.).
    
    Triggered when HTTPException is raised explicitly in the code.
    Returns consistent error format for all HTTP errors.
    
    Args:
        request: The incoming request
        exc: The HTTP exception
        
    Returns:
        JSONResponse with appropriate status code and error details
    """
    # Log the HTTP exception
    log_level = logging.WARNING if exc.status_code < 500 else logging.ERROR
    logger.log(
        log_level,
        f"HTTP {exc.status_code} for {request.method} {request.url.path}: {exc.detail}"
    )
    
    # Create error response
    error_response = ErrorResponse(
        error=ErrorDetail(
            code=exc.status_code,
            message=str(exc.detail)
        )
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump()
    )


async def timeout_exception_handler(
    request: Request,
    exc: asyncio.TimeoutError
) -> JSONResponse:
    """
    Handle AsyncIO timeout errors (504 Gateway Timeout).
    
    Triggered when an async operation exceeds its timeout limit.
    Provides graceful fallback message with retry suggestion.
    
    Args:
        request: The incoming request
        exc: The timeout exception
        
    Returns:
        JSONResponse with 504 status and helpful timeout message
    """
    # Log the timeout
    logger.warning(
        f"Request timeout for {request.method} {request.url.path}",
        extra={"exception_type": type(exc).__name__}
    )
    
    # Create error response with helpful message
    error_response = ErrorResponse(
        error=ErrorDetail(
            code=status.HTTP_504_GATEWAY_TIMEOUT,
            message="Request timed out. Please try again or simplify your question."
        )
    )
    
    return JSONResponse(
        status_code=status.HTTP_504_GATEWAY_TIMEOUT,
        content=error_response.model_dump()
    )


async def general_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """
    Handle unexpected errors (500 Internal Server Error).
    
    Catches all unhandled exceptions to prevent server crashes.
    Logs detailed error information while returning generic message to users.
    
    Args:
        request: The incoming request
        exc: The exception
        
    Returns:
        JSONResponse with 500 status and generic error message
    """
    # Log the full exception with stack trace
    logger.error(
        f"Unexpected error for {request.method} {request.url.path}: {str(exc)}",
        exc_info=True,
        extra={
            "exception_type": type(exc).__name__,
            "exception_message": str(exc)
        }
    )
    
    # Return generic error message (don't expose internal details)
    error_response = ErrorResponse(
        error=ErrorDetail(
            code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="AI service temporarily unavailable. Please try again later."
        )
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump()
    )


def register_exception_handlers(app) -> None:
    """
    Register all exception handlers with the FastAPI application.
    
    This function should be called during application initialization
    to ensure all exceptions are handled consistently.
    
    Args:
        app: The FastAPI application instance
    """
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(asyncio.TimeoutError, timeout_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
    
    logger.info("Exception handlers registered successfully")
