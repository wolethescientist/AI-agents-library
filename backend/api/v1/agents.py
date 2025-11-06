"""
Agents API router for v1 endpoints.

This module provides endpoints for listing available agents and chatting with them.
"""

import asyncio
import logging
import time
import json
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from typing import Annotated

from backend.config import Settings, get_settings
from backend.models.requests import ChatRequest
from backend.models.responses import SuccessResponse, AgentResponse
from backend.services.ai_service import AIService
from backend.agents.config import AgentManager

logger = logging.getLogger(__name__)

# Create router with prefix and tags
router = APIRouter(prefix="/api/v1/agents", tags=["agents"])

# Dependency for getting services
# These will be initialized in main.py and injected
_agent_manager: AgentManager = None
_ai_service: AIService = None


def set_services(agent_manager: AgentManager, ai_service: AIService):
    """Set the service instances for dependency injection.
    
    This function should be called during application startup to initialize
    the services that will be used by the router endpoints.
    
    Args:
        agent_manager: The AgentManager instance
        ai_service: The AIService instance
    """
    global _agent_manager, _ai_service
    _agent_manager = agent_manager
    _ai_service = ai_service
    logger.info("Agents router services initialized")


def get_agent_manager() -> AgentManager:
    """Dependency to get the AgentManager instance.
    
    Returns:
        The AgentManager instance
    
    Raises:
        HTTPException: If the service is not initialized
    """
    if _agent_manager is None:
        logger.error("AgentManager not initialized")
        raise HTTPException(
            status_code=500,
            detail="Service not properly initialized"
        )
    return _agent_manager


def get_ai_service() -> AIService:
    """Dependency to get the AIService instance.
    
    Returns:
        The AIService instance
    
    Raises:
        HTTPException: If the service is not initialized
    """
    if _ai_service is None:
        logger.error("AIService not initialized")
        raise HTTPException(
            status_code=500,
            detail="Service not properly initialized"
        )
    return _ai_service


@router.get(
    "/",
    response_model=SuccessResponse,
    summary="List all available agents",
    description="Returns a list of all enabled AI agents with their metadata",
    responses={
        200: {
            "description": "Successfully retrieved agent list",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": {
                            "agents": [
                                {
                                    "id": "math",
                                    "name": "Mathematics Agent",
                                    "description": "Expert in mathematics, algebra, calculus, geometry, and problem-solving"
                                },
                                {
                                    "id": "english",
                                    "name": "English Language Agent",
                                    "description": "Expert in English grammar, literature, writing, and language arts"
                                }
                            ]
                        },
                        "message": "Found 5 available agents"
                    }
                }
            }
        },
        500: {
            "description": "Internal server error",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": {
                            "code": 500,
                            "message": "Failed to retrieve agent list"
                        }
                    }
                }
            }
        }
    }
)
async def list_agents(
    agent_manager: Annotated[AgentManager, Depends(get_agent_manager)]
) -> SuccessResponse:
    """List all available AI agents.
    
    This endpoint returns metadata for all enabled agents including their ID,
    name, and description. Disabled agents are not included in the response.
    
    **Example Request:**
    ```bash
    curl -X GET "http://localhost:8000/api/v1/agents"
    ```
    
    **Example Response:**
    ```json
    {
        "success": true,
        "data": {
            "agents": [
                {
                    "id": "math",
                    "name": "Mathematics Agent",
                    "description": "Expert in mathematics..."
                },
                {
                    "id": "english",
                    "name": "English Language Agent",
                    "description": "Expert in English..."
                }
            ]
        },
        "message": "Found 5 available agents"
    }
    ```
    
    Args:
        agent_manager: Injected AgentManager dependency
    
    Returns:
        SuccessResponse containing list of agent metadata
    """
    logger.info("Listing all available agents")
    
    try:
        # Get list of enabled agents
        agents = agent_manager.list_agents(include_disabled=False)
        
        logger.info(f"Successfully listed {len(agents)} agents")
        
        return SuccessResponse(
            success=True,
            data={"agents": agents},
            message=f"Found {len(agents)} available agents"
        )
    
    except Exception as e:
        logger.error(f"Error listing agents: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve agent list"
        )


@router.post(
    "/{agent_id}",
    response_model=SuccessResponse,
    summary="Chat with a specific agent",
    description="Send a message to a specific AI agent and receive a response",
    responses={
        200: {
            "description": "Successfully generated response",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": {
                            "agent_id": "math",
                            "agent_name": "Mathematics Agent",
                            "user_message": "What is the Pythagorean theorem?",
                            "reply": "The Pythagorean theorem states that in a right triangle, the square of the length of the hypotenuse (c) equals the sum of squares of the other two sides (a and b): a² + b² = c²",
                            "timestamp": "2025-11-06T10:30:00Z",
                            "metadata": {
                                "processing_time_ms": 1250
                            }
                        },
                        "message": "Response generated successfully"
                    }
                }
            }
        },
        400: {
            "description": "Invalid request (validation error)",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": {
                            "code": 400,
                            "message": "Message exceeds maximum length of 5000 characters"
                        }
                    }
                }
            }
        },
        404: {
            "description": "Agent not found",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": {
                            "code": 404,
                            "message": "Agent 'history' not found. Available agents: math, english, physics, chemistry, civic"
                        }
                    }
                }
            }
        },
        504: {
            "description": "Request timeout",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": {
                            "code": 504,
                            "message": "Request timed out after 15 seconds. Please try again or simplify your question."
                        }
                    }
                }
            }
        },
        500: {
            "description": "Internal server error",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": {
                            "code": 500,
                            "message": "AI service temporarily unavailable. Please try again later."
                        }
                    }
                }
            }
        }
    }
)
async def chat_with_agent(
    agent_id: str,
    request: ChatRequest,
    agent_manager: Annotated[AgentManager, Depends(get_agent_manager)],
    ai_service: Annotated[AIService, Depends(get_ai_service)]
) -> SuccessResponse:
    """Send a message to a specific AI agent and get a response.
    
    This endpoint validates the agent ID, processes the user's message,
    and returns the AI-generated response along with metadata.
    
    **Available Agents:**
    - `math` - Mathematics Agent
    - `english` - English Language Agent
    - `physics` - Physics Agent
    - `chemistry` - Chemistry Agent
    - `civic` - Civic Education Agent
    
    **Example Request:**
    ```bash
    curl -X POST "http://localhost:8000/api/v1/agents/math" \\
         -H "Content-Type: application/json" \\
         -d '{"message": "What is the Pythagorean theorem?"}'
    ```
    
    **Example Response:**
    ```json
    {
        "success": true,
        "data": {
            "agent_id": "math",
            "agent_name": "Mathematics Agent",
            "user_message": "What is the Pythagorean theorem?",
            "reply": "The Pythagorean theorem states...",
            "timestamp": "2025-11-06T10:30:00Z",
            "metadata": {
                "processing_time_ms": 1250
            }
        },
        "message": "Response generated successfully"
    }
    ```
    
    **Error Responses:**
    - **400 Bad Request**: Invalid message (empty, too long, or validation error)
    - **404 Not Found**: Agent ID does not exist or is disabled
    - **504 Gateway Timeout**: Request exceeded 15-second timeout
    - **500 Internal Server Error**: AI service unavailable or unexpected error
    
    Args:
        agent_id: The unique identifier of the agent to chat with
        request: ChatRequest containing the user's message
        agent_manager: Injected AgentManager dependency
        ai_service: Injected AIService dependency
    
    Returns:
        SuccessResponse containing the agent's response and metadata
    
    Raises:
        HTTPException: 404 if agent not found, 504 if timeout, 500 for other errors
    """
    logger.info(f"Chat request for agent '{agent_id}'")
    
    # Track processing time
    start_time = time.time()
    
    try:
        # Validate agent exists and is enabled
        agent = agent_manager.get_agent(agent_id)
        
        # Generate AI response
        reply = await ai_service.generate_response(agent_id, request.message)
        
        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        # Build response data
        agent_response = AgentResponse(
            agent_id=agent.id,
            agent_name=agent.name,
            user_message=request.message,
            reply=reply,
            metadata={
                "processing_time_ms": processing_time_ms
            }
        )
        
        logger.info(
            f"Successfully generated response for agent '{agent_id}' "
            f"in {processing_time_ms}ms"
        )
        
        return SuccessResponse(
            success=True,
            data=agent_response.model_dump(),
            message="Response generated successfully"
        )
    
    except KeyError as e:
        # Agent not found or disabled
        logger.warning(f"Agent not found: {e}")
        
        # Get list of available agents for helpful error message
        available_agents = ", ".join(agent_manager.list_agent_ids())
        
        raise HTTPException(
            status_code=404,
            detail=f"Agent '{agent_id}' not found. Available agents: {available_agents}"
        )
    
    except TimeoutError as e:
        # Request timeout
        logger.warning(f"Request timeout for agent '{agent_id}': {e}")
        raise HTTPException(
            status_code=504,
            detail=str(e)
        )
    
    except Exception as e:
        # Other errors
        logger.error(
            f"Error processing chat request for agent '{agent_id}': {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="AI service temporarily unavailable. Please try again later."
        )


@router.post(
    "/{agent_id}/stream",
    summary="Chat with a specific agent (streaming)",
    description="Send a message to a specific AI agent and receive a streaming response",
    responses={
        200: {
            "description": "Successfully streaming response",
            "content": {
                "text/event-stream": {
                    "example": 'data: {"chunk": "The Pythagorean"}\n\ndata: {"chunk": " theorem states"}\n\ndata: {"done": true}\n\n'
                }
            }
        },
        404: {
            "description": "Agent not found"
        },
        504: {
            "description": "Request timeout"
        },
        500: {
            "description": "Internal server error"
        }
    }
)
async def chat_with_agent_stream(
    agent_id: str,
    request: ChatRequest,
    agent_manager: Annotated[AgentManager, Depends(get_agent_manager)],
    ai_service: Annotated[AIService, Depends(get_ai_service)]
):
    """Send a message to a specific AI agent and get a streaming response.
    
    This endpoint provides Server-Sent Events (SSE) streaming for real-time
    token-by-token responses, significantly improving perceived response time.
    
    **Example Request:**
    ```bash
    curl -X POST "http://localhost:8000/api/v1/agents/math/stream" \\
         -H "Content-Type: application/json" \\
         -d '{"message": "What is the Pythagorean theorem?"}'
    ```
    
    **Example Response (SSE format):**
    ```
    data: {"chunk": "The Pythagorean"}
    
    data: {"chunk": " theorem states"}
    
    data: {"chunk": " that in a"}
    
    data: {"done": true, "metadata": {"processing_time_ms": 1250}}
    ```
    
    Args:
        agent_id: The unique identifier of the agent to chat with
        request: ChatRequest containing the user's message
        agent_manager: Injected AgentManager dependency
        ai_service: Injected AIService dependency
    
    Returns:
        StreamingResponse with Server-Sent Events
    
    Raises:
        HTTPException: 404 if agent not found, 504 if timeout, 500 for other errors
    """
    logger.info(f"Streaming chat request for agent '{agent_id}'")
    
    start_time = time.time()
    
    try:
        # Validate agent exists and is enabled
        agent = agent_manager.get_agent(agent_id)
        
        async def event_generator():
            """Generate SSE events for streaming response."""
            try:
                # Stream chunks from AI service
                async for chunk in ai_service.generate_response_stream(agent_id, request.message):
                    # Send chunk as SSE
                    yield f"data: {json.dumps({'chunk': chunk})}\n\n"
                
                # Calculate processing time
                processing_time_ms = int((time.time() - start_time) * 1000)
                
                # Send completion event
                yield f"data: {json.dumps({'done': True, 'metadata': {'processing_time_ms': processing_time_ms}})}\n\n"
                
                logger.info(
                    f"Successfully completed streaming response for agent '{agent_id}' "
                    f"in {processing_time_ms}ms"
                )
                
            except asyncio.TimeoutError as e:
                # Send timeout error
                yield f"data: {json.dumps({'error': str(e), 'code': 504})}\n\n"
                logger.warning(f"Request timeout for agent '{agent_id}': {e}")
                
            except Exception as e:
                # Send error event
                yield f"data: {json.dumps({'error': 'AI service temporarily unavailable', 'code': 500})}\n\n"
                logger.error(
                    f"Error in streaming response for agent '{agent_id}': {e}",
                    exc_info=True
                )
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # Disable nginx buffering
            }
        )
    
    except KeyError as e:
        # Agent not found or disabled
        logger.warning(f"Agent not found: {e}")
        available_agents = ", ".join(agent_manager.list_agent_ids())
        raise HTTPException(
            status_code=404,
            detail=f"Agent '{agent_id}' not found. Available agents: {available_agents}"
        )
    
    except Exception as e:
        # Other errors
        logger.error(
            f"Error setting up streaming for agent '{agent_id}': {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="AI service temporarily unavailable. Please try again later."
        )
