"""
Centralized exception handlers for the FastAPI application.
Ensures consistent error response format across all endpoints.
"""
import logging
import asyncio
from typing import Optional, Dict, Any
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException
from pydantic import ValidationError

from backend.models.responses import ErrorResponse, ErrorDetail


logger = logging.getLogger(__name__)


def create_detailed_error_response(
    code: int,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    suggestion: Optional[str] = None
) -> ErrorResponse:
    """
    Create a detailed error response with helpful context for frontend developers.
    
    Args:
        code: HTTP status code
        message: Main error message
        details: Additional error details (field errors, validation info, etc.)
        suggestion: Helpful suggestion for fixing the error
        
    Returns:
        ErrorResponse with comprehensive error information
    """
    error_detail = ErrorDetail(code=code, message=message)
    
    # Add optional fields if provided
    if details:
        error_detail.details = details
    if suggestion:
        error_detail.suggestion = suggestion
    
    return ErrorResponse(error=error_detail)


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
    
    # Build detailed error information for frontend developers
    field_errors = []
    for error in errors:
        # Get the field path (excluding 'body')
        field_path = [str(loc) for loc in error["loc"] if loc != "body"]
        field_name = " -> ".join(field_path) if field_path else "request"
        
        field_errors.append({
            "field": field_name,
            "message": error["msg"],
            "type": error["type"],
            "input": error.get("input")
        })
    
    # Build user-friendly main message
    if len(field_errors) == 1:
        error = field_errors[0]
        message = f"Validation error in '{error['field']}': {error['message']}"
    else:
        message = f"Request validation failed with {len(field_errors)} error(s)"
    
    # Log the validation error
    logger.warning(
        f"Validation error for {request.method} {request.url.path}: {message}",
        extra={"errors": errors, "request_body": await request.body()}
    )
    
    # Create detailed error response
    error_response = create_detailed_error_response(
        code=status.HTTP_400_BAD_REQUEST,
        message=message,
        details={
            "validation_errors": field_errors,
            "endpoint": str(request.url.path),
            "method": request.method
        },
        suggestion="Check the API documentation for required fields and data types. Ensure all required fields are present and have the correct format."
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
    
    # Add helpful suggestions based on status code
    suggestion = None
    details = {
        "endpoint": str(request.url.path),
        "method": request.method
    }
    
    if exc.status_code == 404:
        suggestion = "Verify the endpoint URL and any resource IDs (agent_id, session_id) are correct. Check the API documentation for valid endpoints."
    elif exc.status_code == 413:
        suggestion = "Reduce the file size or compress the file before uploading. Maximum allowed size is 30 MB."
    elif exc.status_code == 422:
        suggestion = "Ensure the file type is supported. Allowed types: PDF, PNG, JPG, JPEG, HEIC."
    elif exc.status_code == 429:
        suggestion = "You've exceeded the rate limit. Wait a moment before retrying. Consider implementing exponential backoff in your client."
        details["retry_after"] = exc.headers.get("Retry-After") if hasattr(exc, "headers") else None
    elif exc.status_code == 504:
        suggestion = "The request took too long to process. Try with a smaller file, simpler query, or retry the request."
    elif exc.status_code >= 500:
        suggestion = "This is a server-side error. Please try again in a few moments. If the issue persists, contact support."
    
    # Create detailed error response
    error_response = create_detailed_error_response(
        code=exc.status_code,
        message=str(exc.detail),
        details=details,
        suggestion=suggestion
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
    
    # Determine timeout context based on endpoint
    is_file_upload = "file" in str(request.url.path).lower() or request.method == "POST"
    
    message = "Request timed out while processing"
    suggestion = "Retry the request. "
    
    if is_file_upload:
        message = "File processing timed out. The file may be too large or complex."
        suggestion += "Try with a smaller file, reduce file complexity (fewer pages/lower resolution), or increase client timeout settings."
    else:
        message = "Request timed out. The operation took too long to complete."
        suggestion += "Simplify your query, reduce the amount of data being processed, or increase client timeout settings."
    
    # Create detailed error response
    error_response = create_detailed_error_response(
        code=status.HTTP_504_GATEWAY_TIMEOUT,
        message=message,
        details={
            "endpoint": str(request.url.path),
            "method": request.method,
            "timeout_type": "processing"
        },
        suggestion=suggestion
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
    Logs detailed error information while returning helpful message to developers.
    
    Args:
        request: The incoming request
        exc: The exception
        
    Returns:
        JSONResponse with 500 status and helpful error message
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
    
    # Provide helpful context based on exception type
    exception_type = type(exc).__name__
    message = "An unexpected error occurred while processing your request"
    
    details = {
        "endpoint": str(request.url.path),
        "method": request.method,
        "error_type": exception_type
    }
    
    # Add specific guidance for common exception types
    suggestion = "Please try again. If the issue persists, contact support with the error details."
    
    if "Connection" in exception_type or "Network" in exception_type:
        message = "Network or connection error occurred"
        suggestion = "Check network connectivity and ensure all required services (OpenAI API, database) are accessible. Verify API keys and credentials are correct."
    elif "Timeout" in exception_type:
        message = "Operation timed out"
        suggestion = "The operation took too long. Try with smaller inputs or increase timeout settings."
    elif "Memory" in exception_type:
        message = "Memory limit exceeded"
        suggestion = "The operation required too much memory. Try processing smaller files or reducing batch sizes."
    elif "Permission" in exception_type or "Auth" in exception_type:
        message = "Permission or authentication error"
        suggestion = "Verify API keys and credentials are correctly configured in environment variables."
    
    # Create detailed error response
    error_response = create_detailed_error_response(
        code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        message=message,
        details=details,
        suggestion=suggestion
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
