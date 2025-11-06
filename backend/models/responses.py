"""
Response models for API endpoints.
"""
from pydantic import BaseModel, Field
from typing import Any, Dict, Optional
from datetime import datetime


class ErrorDetail(BaseModel):
    """Error detail structure."""
    
    code: int = Field(..., description="HTTP status code")
    message: str = Field(..., description="Error message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "code": 404,
                "message": "Agent not found"
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response structure."""
    
    success: bool = Field(default=False, description="Always false for errors")
    error: ErrorDetail = Field(..., description="Error details")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": {
                    "code": 404,
                    "message": "Agent 'history' not found. Available agents: math, english, physics, chemistry, civic"
                }
            }
        }


class SuccessResponse(BaseModel):
    """Standard success response structure."""
    
    success: bool = Field(default=True, description="Always true for success")
    data: Dict[str, Any] = Field(..., description="Response data")
    message: str = Field(default="", description="Optional success message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "agent_id": "math",
                    "agent_name": "Mathematics Agent",
                    "reply": "The Pythagorean theorem states..."
                },
                "message": "Response generated successfully"
            }
        }


class AgentResponse(BaseModel):
    """Agent chat response data structure."""
    
    agent_id: str = Field(..., description="Agent identifier")
    agent_name: str = Field(..., description="Agent display name")
    user_message: str = Field(..., description="Original user message")
    reply: str = Field(..., description="Agent's reply")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Response timestamp"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "agent_id": "math",
                "agent_name": "Mathematics Agent",
                "user_message": "What is the Pythagorean theorem?",
                "reply": "The Pythagorean theorem states that in a right triangle...",
                "timestamp": "2025-11-06T10:30:00Z",
                "metadata": {
                    "processing_time_ms": 1250
                }
            }
        }
