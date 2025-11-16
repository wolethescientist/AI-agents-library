"""
Response models for API endpoints.
"""
from pydantic import BaseModel, Field
from typing import Any, Dict, Optional
from datetime import datetime


class ErrorDetail(BaseModel):
    """Enhanced error detail structure with developer-friendly information."""
    
    code: int = Field(..., description="HTTP status code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional error details (validation errors, context, etc.)"
    )
    suggestion: Optional[str] = Field(
        None,
        description="Helpful suggestion for resolving the error"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "code": 404,
                "message": "Agent 'history' not found",
                "details": {
                    "endpoint": "/api/v1/agents/history",
                    "method": "POST",
                    "available_agents": ["math", "english", "physics", "chemistry", "civic"]
                },
                "suggestion": "Verify the agent_id is correct. Check the API documentation for valid agent IDs."
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
    privacy: Optional[str] = Field(default=None, description="Privacy guarantee message")
    
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


class AgentChatResponse(BaseModel):
    """Enhanced agent response with mode detection and document context support."""
    
    agent_id: str = Field(..., description="Agent identifier")
    agent_name: str = Field(..., description="Agent display name")
    mode: str = Field(..., description="Response mode: 'general' or 'document'")
    message_type: str = Field(..., description="Message type: 'text', 'file_ack', or 'answer'")
    user_message: str = Field(..., description="Original user message")
    reply: str = Field(..., description="Agent's reply")
    session_id: Optional[str] = Field(None, description="Session ID if document context is active")
    source_chunks: Optional[list] = Field(None, description="Source chunks from document (RAG mode)")
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
                "agent_id": "physics",
                "agent_name": "Physics Agent",
                "mode": "document",
                "message_type": "answer",
                "user_message": "What's question 2 about?",
                "reply": "Question 2 on page 2 asks about projectile motion...",
                "session_id": "s_Ab3xYz...",
                "source_chunks": [
                    {
                        "page": 2,
                        "excerpt": "Question 2: A projectile is launched...",
                        "type": "text"
                    }
                ],
                "timestamp": "2025-11-10T10:30:00Z",
                "metadata": {
                    "processing_time_ms": 1500,
                    "chunks_retrieved": 3
                }
            }
        }
