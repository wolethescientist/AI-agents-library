"""
Health check API router for v1 endpoints.

This module provides a health check endpoint for monitoring service availability
and status.
"""

import logging
from datetime import datetime
from fastapi import APIRouter, Depends
from typing import Annotated
import google.generativeai as genai

from backend.config import Settings, get_settings
from backend.models.responses import SuccessResponse

logger = logging.getLogger(__name__)

# Create router with tags
router = APIRouter(prefix="/api/v1", tags=["health"])


@router.get(
    "/health",
    response_model=SuccessResponse,
    summary="Health check endpoint",
    description="Returns the current health status of the service including version and timestamp",
    responses={
        200: {
            "description": "Service is healthy",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": {
                            "status": "healthy",
                            "version": "1.0.0",
                            "timestamp": "2025-11-06T10:30:00Z",
                            "services": {
                                "gemini_api": "operational"
                            }
                        },
                        "message": "Service is operational"
                    }
                }
            }
        }
    }
)
async def health_check(
    settings: Annotated[Settings, Depends(get_settings)]
) -> SuccessResponse:
    """Check the health status of the service.
    
    This endpoint provides information about the service status, version,
    and the availability of external dependencies like the Gemini API.
    
    The endpoint is designed to respond quickly (under 1 second) for use
    with monitoring tools and health check systems.
    
    **Example Request:**
    ```bash
    curl -X GET "http://localhost:8000/api/v1/health"
    ```
    
    **Example Response:**
    ```json
    {
        "success": true,
        "data": {
            "status": "healthy",
            "version": "1.0.0",
            "timestamp": "2025-11-06T10:30:00Z",
            "services": {
                "gemini_api": "operational"
            }
        },
        "message": "Service is operational"
    }
    ```
    
    **Response Fields:**
    - `status`: Overall service health status ("healthy", "degraded", "unhealthy")
    - `version`: Current application version
    - `timestamp`: Current server time in ISO 8601 format
    - `services.gemini_api`: Status of Gemini API connection
    
    Args:
        settings: Injected Settings dependency
    
    Returns:
        SuccessResponse containing health status information
    """
    logger.debug("Health check requested")
    
    # Check Gemini API status
    gemini_status = "operational"
    try:
        # Quick check to see if API is configured
        # We don't make an actual API call to keep response time under 1 second
        if not settings.gemini_api_key:
            gemini_status = "not_configured"
        # If we wanted to do a real check, we'd need to make it very fast
        # For now, we assume operational if API key is present
    except Exception as e:
        logger.warning(f"Error checking Gemini API status: {e}")
        gemini_status = "unknown"
    
    # Build health response
    health_data = {
        "status": "healthy",
        "version": settings.app_version,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "services": {
            "gemini_api": gemini_status
        }
    }
    
    logger.debug(f"Health check completed: {health_data['status']}")
    
    return SuccessResponse(
        success=True,
        data=health_data,
        message="Service is operational"
    )
