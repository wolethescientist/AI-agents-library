"""
Request models for API endpoints.
"""
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
