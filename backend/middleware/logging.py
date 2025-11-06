"""
Logging middleware for request/response tracking and performance monitoring.
Provides structured logging for all API requests with timing information.
"""
import logging
import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging HTTP requests and responses with performance metrics.
    
    Logs:
    - Request method, path, and timestamp on request start
    - Response status code and processing time on request completion
    - Structured format for easy parsing and monitoring
    
    Requirements: 9.1, 9.2, 9.3, 9.4, 9.5
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and log details with performance metrics.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware or route handler
            
        Returns:
            Response from the application
        """
        # Record start time for performance tracking
        start_time = time.time()
        
        # Extract request details
        method = request.method
        path = request.url.path
        client_host = request.client.host if request.client else "unknown"
        
        # Log incoming request (Requirement 9.1)
        logger.info(
            f"Request started | method={method} path={path} client={client_host}"
        )
        
        # Process request and handle any errors
        try:
            response = await call_next(request)
            status_code = response.status_code
            
        except Exception as exc:
            # Log error details (Requirement 9.3)
            processing_time = time.time() - start_time
            logger.error(
                f"Request failed | method={method} path={path} "
                f"error={str(exc)} duration={processing_time:.3f}s",
                exc_info=True
            )
            raise
        
        # Calculate processing time (Requirement 9.5)
        processing_time = time.time() - start_time
        
        # Log response with performance metrics (Requirement 9.2)
        log_message = (
            f"Request completed | method={method} path={path} "
            f"status={status_code} duration={processing_time:.3f}s"
        )
        
        # Use appropriate log level based on status code
        if status_code >= 500:
            logger.error(log_message)
        elif status_code >= 400:
            logger.warning(log_message)
        else:
            logger.info(log_message)
        
        # Add performance metric to response headers for monitoring
        response.headers["X-Process-Time"] = f"{processing_time:.3f}"
        
        return response


async def logging_middleware_function(request: Request, call_next: Callable) -> Response:
    """
    Functional middleware for logging requests and responses.
    Alternative to class-based middleware for simpler integration.
    
    Args:
        request: Incoming HTTP request
        call_next: Next middleware or route handler
        
    Returns:
        Response from the application
    """
    # Record start time for performance tracking
    start_time = time.time()
    
    # Extract request details
    method = request.method
    path = request.url.path
    client_host = request.client.host if request.client else "unknown"
    
    # Log incoming request (Requirement 9.1)
    logger.info(
        f"Request started | method={method} path={path} client={client_host}"
    )
    
    # Process request and handle any errors
    try:
        response = await call_next(request)
        status_code = response.status_code
        
    except Exception as exc:
        # Log error details (Requirement 9.3)
        processing_time = time.time() - start_time
        logger.error(
            f"Request failed | method={method} path={path} "
            f"error={str(exc)} duration={processing_time:.3f}s",
            exc_info=True
        )
        raise
    
    # Calculate processing time (Requirement 9.5)
    processing_time = time.time() - start_time
    
    # Log response with performance metrics (Requirement 9.2)
    log_message = (
        f"Request completed | method={method} path={path} "
        f"status={status_code} duration={processing_time:.3f}s"
    )
    
    # Use appropriate log level based on status code
    if status_code >= 500:
        logger.error(log_message)
    elif status_code >= 400:
        logger.warning(log_message)
    else:
        logger.info(log_message)
    
    # Add performance metric to response headers for monitoring
    response.headers["X-Process-Time"] = f"{processing_time:.3f}"
    
    return response
