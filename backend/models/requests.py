"""
Request models for API endpoints.
"""
from typing import Optional
from pydantic import BaseModel, Field, validator


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    
    message: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="User message to send to the agent"
    )
    
    @validator('message')
    def sanitize_message(cls, v):
        """Sanitize and validate message."""
        # Strip whitespace
        v = v.strip()
        
        # Ensure not empty after stripping
        if not v:
            raise ValueError("Message cannot be empty or only whitespace")
        
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "What is the Pythagorean theorem?"
            }
        }


class DocumentQueryRequest(BaseModel):
    """Request model for document query endpoint."""
    
    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Question about the uploaded document"
    )
    
    @validator('message')
    def sanitize_message(cls, v):
        """Sanitize and validate message."""
        v = v.strip()
        if not v:
            raise ValueError("Message cannot be empty or only whitespace")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "What are the main points discussed in this document?"
            }
        }


class AgentChatRequest(BaseModel):
    """Enhanced chat request with optional session context for document-based conversations."""
    
    message: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="User message to send to the agent"
    )
    
    session_id: Optional[str] = Field(
        None,
        description="Optional session ID for document context continuation"
    )
    
    @validator('message')
    def sanitize_message(cls, v):
        """Sanitize and validate message."""
        v = v.strip()
        if not v:
            raise ValueError("Message cannot be empty or only whitespace")
        return v
    
    @validator('session_id')
    def validate_session_id(cls, v):
        """Validate session ID format."""
        if v is not None:
            v = v.strip()
            if not v.startswith('s_'):
                raise ValueError("Invalid session ID format")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "What's on page 2?",
                "session_id": "s_Ab3xYz..."
            }
        }
