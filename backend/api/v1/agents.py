"""
Agents API router for v1 endpoints.

This module provides endpoints for listing available agents and chatting with them.
"""

import asyncio
import logging
import time
import json
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Form, File, UploadFile
from fastapi.responses import StreamingResponse
from typing import Annotated, Optional

from backend.config import Settings, get_settings
from backend.models.responses import SuccessResponse, AgentResponse
from backend.services.ai_service import AIService
from backend.services.rag_service import RAGService
from backend.agents.config import AgentManager

logger = logging.getLogger(__name__)

# Create router with prefix and tags
router = APIRouter(prefix="/api/v1/agents", tags=["agents"])

# Configuration constants for file uploads
MAX_FILE_SIZE = 30 * 1024 * 1024  # 30 MB
ALLOWED_PDF_TYPES = ["application/pdf"]
ALLOWED_IMAGE_TYPES = ["image/png", "image/jpeg", "image/jpg", "image/heic"]


def validate_file(file: UploadFile) -> None:
    """Validate uploaded file type.
    
    Args:
        file: The uploaded file
    
    Raises:
        HTTPException: If file type is not supported
    """
    allowed_types = ALLOWED_PDF_TYPES + ALLOWED_IMAGE_TYPES
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported file type '{file.content_type}'. "
                   f"Supported types: PDF, PNG, JPG, JPEG, HEIC. "
                   f"Ensure your file has the correct MIME type and extension."
        )




# Dependency for getting services
# These will be initialized in main.py and injected
_agent_manager: AgentManager = None
_ai_service: AIService = None
_rag_service: RAGService = None


def set_services(agent_manager: AgentManager, ai_service: AIService, rag_service: RAGService):
    """Set the service instances for dependency injection.
    
    This function should be called during application startup to initialize
    the services that will be used by the router endpoints.
    
    Args:
        agent_manager: The AgentManager instance
        ai_service: The AIService instance
        rag_service: The RAGService instance
    """
    global _agent_manager, _ai_service, _rag_service
    _agent_manager = agent_manager
    _ai_service = ai_service
    _rag_service = rag_service
    logger.info("Agents router services initialized (including RAG service)")


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
            detail="AgentManager service not initialized. This is a server configuration issue. "
                   "Ensure the application started correctly and all dependencies are loaded."
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
            detail="AIService not initialized. This is a server configuration issue. "
                   "Verify OPENAI_API_KEY is set and the application started correctly."
        )
    return _ai_service


def get_rag_service() -> RAGService:
    """Dependency to get the RAGService instance.
    
    Returns:
        The RAGService instance
    
    Raises:
        HTTPException: If the service is not initialized
    """
    if _rag_service is None:
        logger.error("RAGService not initialized")
        raise HTTPException(
            status_code=500,
            detail="RAGService not initialized. This is a server configuration issue. "
                   "Verify OPENAI_API_KEY is set and the application started correctly."
        )
    return _rag_service


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
    summary="Chat with a specific agent (with file upload support)",
    description="Send a message to a specific AI agent with optional file upload and document context",
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
    agent_manager: Annotated[AgentManager, Depends(get_agent_manager)],
    ai_service: Annotated[AIService, Depends(get_ai_service)],
    rag_service: Annotated[RAGService, Depends(get_rag_service)],
    message: str = Form(..., description="User message"),
    session_id: Optional[str] = Form(None, description="Optional session ID for document context"),
    file: Optional[UploadFile] = File(None, description="Optional PDF or image file")
) -> SuccessResponse:
    """Send a message to a specific AI agent with optional file upload and document context.
    
    This enhanced endpoint supports three modes:
    1. **File Upload**: Upload a PDF or image to create a document session
    2. **Document Query**: Query an uploaded document using session_id
    3. **General Chat**: Standard text-only conversation (backward compatible)
    
    **Available Agents:**
    - `math` - Mathematics Agent
    - `english` - English Language Agent
    - `physics` - Physics Agent
    - `chemistry` - Chemistry Agent
    - `civic` - Civic Education Agent
    
    **Example 1: File Upload**
    ```bash
    curl -X POST "http://localhost:8000/api/v1/agents/physics" \\
         -F "message=Help me with this homework" \\
         -F "file=@homework.pdf"
    ```
    
    **Example 2: Document Query**
    ```bash
    curl -X POST "http://localhost:8000/api/v1/agents/physics" \\
         -F "message=What's question 2?" \\
         -F "session_id=s_xyz123"
    ```
    
    **Example 3: General Chat (JSON)**
    ```bash
    curl -X POST "http://localhost:8000/api/v1/agents/physics" \\
         -H "Content-Type: application/json" \\
         -d '{"message": "What is Newton'\''s second law?"}'
    ```
    
    Args:
        agent_id: The unique identifier of the agent to chat with
        message: User's message or question
        session_id: Optional session ID for document context
        file: Optional PDF or image file upload
        agent_manager: Injected AgentManager dependency
        ai_service: Injected AIService dependency
        rag_service: Injected RAGService dependency
    
    Returns:
        SuccessResponse with mode, message_type, and appropriate response data
    
    Raises:
        HTTPException: Various status codes for different error conditions
    """
    logger.info(f"Enhanced chat request for agent '{agent_id}' (file={file is not None}, session={session_id})")
    
    start_time = time.time()
    
    try:
        # Validate agent exists and is enabled
        agent = agent_manager.get_agent(agent_id)
        
        # CASE 1: File Upload - Process document and create session
        if file is not None:
            logger.info(f"Processing file upload: {file.filename}")
            
            # Validate file type
            validate_file(file)
            
            # Read file content
            file_bytes = await file.read()
            file_size = len(file_bytes)
            
            # Validate file size
            if file_size > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=413,
                    detail=f"File too large: {file_size / 1024 / 1024:.1f} MB. "
                           f"Maximum allowed: {MAX_FILE_SIZE / 1024 / 1024:.0f} MB. "
                           f"Compress the file or reduce its size before uploading."
                )
            
            if file_size == 0:
                raise HTTPException(
                    status_code=400,
                    detail="File is empty (0 bytes). Ensure the file contains data and was uploaded correctly."
                )
            
            logger.info(f"File validated: size={file_size / 1024:.1f} KB")
            
            # Process based on file type
            if file.content_type in ALLOWED_PDF_TYPES:
                new_session_id = await rag_service.process_pdf(file_bytes)
                doc_type = "pdf"
            else:
                new_session_id = await rag_service.process_image(file_bytes)
                doc_type = "image"
            
            # Get session info
            session_info = rag_service.session_manager.get_session_info(new_session_id)
            
            # Calculate processing time
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # Generate acknowledgment message
            if doc_type == "pdf":
                pages = session_info.get("metadata", {}).get("text_chunks", 0) // 2 or "several"
                ack_message = f"I've processed your PDF document ({pages} pages). I can help you understand the content and answer questions about it. What would you like to know?"
            else:
                ack_message = "I've processed your image. I can help you understand what's in it. What would you like to know?"
            
            logger.info(f"File processed successfully: session={new_session_id}, time={processing_time_ms}ms")
            
            return SuccessResponse(
                success=True,
                data={
                    "agent_id": agent.id,
                    "agent_name": agent.name,
                    "mode": "document",
                    "message_type": "file_ack",
                    "user_message": message,
                    "reply": ack_message,
                    "session_id": new_session_id,
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "metadata": {
                        "processing_time_ms": processing_time_ms,
                        "document_type": doc_type,
                        **session_info.get("metadata", {})
                    }
                },
                message="Document processed successfully",
                privacy="Uploaded file is processed in memory only and will be removed after 20 minutes."
            )
        
        # CASE 2: Query with Session Context
        elif session_id is not None:
            logger.info(f"Processing query with session: {session_id}")
            
            # Validate session exists
            session = rag_service.session_manager.get_session(session_id)
            if session is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Session '{session_id}' not found or expired. "
                           f"Sessions expire after 20 minutes of inactivity. "
                           f"Upload a new document to create a new session."
                )
            
            # Always try RAG first when session is active
            # The RAG service will intelligently determine if query is about the document
            logger.info(f"Querying document session with intelligent fallback")
            result = await rag_service.query_session(
                session_id=session_id,
                query=message,
                top_k=5
            )
            
            # Check if RAG determined this is a general query (not about document)
            if result["reply"] is None or result["metadata"].get("fallback_to_general"):
                # Fallback to general agent chat
                logger.info(f"RAG detected general query, using agent mode")
                reply = await ai_service.generate_response(agent_id, message)
                
                processing_time_ms = int((time.time() - start_time) * 1000)
                
                return SuccessResponse(
                    success=True,
                    data={
                        "agent_id": agent.id,
                        "agent_name": agent.name,
                        "mode": "general",
                        "message_type": "text",
                        "user_message": message,
                        "reply": reply,
                        "session_id": session_id,  # Keep session alive
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                        "metadata": {
                            "processing_time_ms": processing_time_ms,
                            "fallback_reason": "general_knowledge_query"
                        }
                    },
                    message="Response generated successfully"
                )
            
            # Document-based answer
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            return SuccessResponse(
                success=True,
                data={
                    "agent_id": agent.id,
                    "agent_name": agent.name,
                    "mode": "document",
                    "message_type": "answer",
                    "user_message": message,
                    "reply": result["reply"],
                    "session_id": session_id,
                    "source_chunks": result["source_chunks"],
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "metadata": {
                        "processing_time_ms": processing_time_ms,
                        "chunks_retrieved": result["metadata"].get("chunks_retrieved", 0)
                    }
                },
                message="Answer generated from document"
                )
        
        # CASE 3: Standard Chat (no file, no session) - Backward compatible
        else:
            logger.info(f"Processing standard chat request")
            
            # Generate AI response
            reply = await ai_service.generate_response(agent_id, message)
            
            # Calculate processing time
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            logger.info(f"Successfully generated response for agent '{agent_id}' in {processing_time_ms}ms")
            
            return SuccessResponse(
                success=True,
                data={
                    "agent_id": agent.id,
                    "agent_name": agent.name,
                    "mode": "general",
                    "message_type": "text",
                    "user_message": message,
                    "reply": reply,
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "metadata": {
                        "processing_time_ms": processing_time_ms
                    }
                },
                message="Response generated successfully"
            )
    
    except HTTPException:
        raise
    
    except KeyError as e:
        # Agent not found or disabled
        logger.warning(f"Agent not found: {e}")
        available_agents = ", ".join(agent_manager.list_agent_ids())
        raise HTTPException(
            status_code=404,
            detail=f"Agent '{agent_id}' not found. Available agents: {available_agents}"
        )
    
    except asyncio.TimeoutError as e:
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
    summary="Chat with a specific agent (streaming with file upload support)",
    description="Send a message to a specific AI agent with optional file upload and receive a streaming response",
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
    agent_manager: Annotated[AgentManager, Depends(get_agent_manager)],
    ai_service: Annotated[AIService, Depends(get_ai_service)],
    rag_service: Annotated[RAGService, Depends(get_rag_service)],
    message: str = Form(..., description="User message"),
    session_id: Optional[str] = Form(None, description="Optional session ID for document context"),
    file: Optional[UploadFile] = File(None, description="Optional PDF or image file")
):
    """Send a message to a specific AI agent with optional file upload and get a streaming response.
    
    This endpoint provides Server-Sent Events (SSE) streaming for real-time responses.
    Supports file uploads and document context like the non-streaming endpoint.
    
    **Example 1: Standard Streaming**
    ```bash
    curl -X POST "http://localhost:8000/api/v1/agents/math/stream" \\
         -F "message=What is the Pythagorean theorem?"
    ```
    
    **Example 2: With File Upload**
    ```bash
    curl -X POST "http://localhost:8000/api/v1/agents/physics/stream" \\
         -F "message=Help me solve this" \\
         -F "file=@homework.pdf"
    ```
    
    Args:
        agent_id: The unique identifier of the agent to chat with
        message: User's message or question
        session_id: Optional session ID for document context
        file: Optional PDF or image file upload
        agent_manager: Injected AgentManager dependency
        ai_service: Injected AIService dependency
        rag_service: Injected RAGService dependency
    
    Returns:
        StreamingResponse with Server-Sent Events
    
    Raises:
        HTTPException: 404 if agent not found, 504 if timeout, 500 for other errors
    """
    logger.info(f"Streaming chat request for agent '{agent_id}' (file={file is not None}, session={session_id})")
    
    start_time = time.time()
    
    try:
        # Validate agent exists and is enabled
        agent = agent_manager.get_agent(agent_id)
        
        async def event_generator():
            """Generate SSE events for streaming response."""
            try:
                # CASE 1: File Upload - Process and send acknowledgment
                if file is not None:
                    logger.info(f"Processing file upload in streaming mode: {file.filename}")
                    
                    # Validate file type
                    validate_file(file)
                    
                    # Read file content
                    file_bytes = await file.read()
                    file_size = len(file_bytes)
                    
                    # Validate file size
                    if file_size > MAX_FILE_SIZE:
                        yield f"data: {json.dumps({'error': 'File too large', 'code': 413})}\n\n"
                        return
                    
                    if file_size == 0:
                        yield f"data: {json.dumps({'error': 'File is empty', 'code': 400})}\n\n"
                        return
                    
                    # Send processing status
                    yield f"data: {json.dumps({'status': 'processing', 'message': 'Processing your document...'})}\n\n"
                    
                    # Process based on file type
                    if file.content_type in ALLOWED_PDF_TYPES:
                        new_session_id = await rag_service.process_pdf(file_bytes)
                        doc_type = "pdf"
                    else:
                        new_session_id = await rag_service.process_image(file_bytes)
                        doc_type = "image"
                    
                    # Get session info
                    session_info = rag_service.session_manager.get_session_info(new_session_id)
                    
                    # Generate acknowledgment
                    if doc_type == "pdf":
                        pages = session_info.get("metadata", {}).get("text_chunks", 0) // 2 or "several"
                        ack_message = f"I've processed your PDF document ({pages} pages). I can help you understand the content and answer questions about it. What would you like to know?"
                    else:
                        ack_message = "I've processed your image. I can help you understand what's in it. What would you like to know?"
                    
                    # Stream the acknowledgment
                    for word in ack_message.split():
                        yield f"data: {json.dumps({'chunk': word + ' '})}\n\n"
                        await asyncio.sleep(0.02)  # Small delay for streaming effect
                    
                    # Send completion
                    processing_time_ms = int((time.time() - start_time) * 1000)
                    yield f"data: {json.dumps({'done': True, 'session_id': new_session_id, 'mode': 'document', 'message_type': 'file_ack', 'metadata': {'processing_time_ms': processing_time_ms}})}\n\n"
                    
                    logger.info(f"File processed successfully in streaming mode: session={new_session_id}")
                
                # CASE 2: Query with Session Context
                elif session_id is not None:
                    logger.info(f"Processing streaming query with session: {session_id}")
                    
                    # Validate session exists
                    session = rag_service.session_manager.get_session(session_id)
                    if session is None:
                        yield f"data: {json.dumps({'error': 'Session not found or expired', 'code': 404})}\n\n"
                        return
                    
                    # Always try RAG first - it will intelligently determine if query is about document
                    result = await rag_service.query_session(session_id, message, top_k=5)
                    
                    # Check if RAG determined this is a general query
                    if result["reply"] is None or result["metadata"].get("fallback_to_general"):
                        # Fallback to general streaming
                        logger.info("RAG detected general query, using agent streaming mode")
                        async for chunk in ai_service.generate_response_stream(agent_id, message):
                            yield f"data: {json.dumps({'chunk': chunk})}\n\n"
                        
                        # Send completion
                        processing_time_ms = int((time.time() - start_time) * 1000)
                        yield f"data: {json.dumps({'done': True, 'session_id': session_id, 'mode': 'general', 'message_type': 'text', 'metadata': {'processing_time_ms': processing_time_ms, 'fallback_reason': 'general_knowledge_query'}})}\n\n"
                    else:
                        # Stream the document-based response
                        for word in result["reply"].split():
                            yield f"data: {json.dumps({'chunk': word + ' '})}\n\n"
                            await asyncio.sleep(0.02)
                        
                        # Send completion
                        processing_time_ms = int((time.time() - start_time) * 1000)
                        yield f"data: {json.dumps({'done': True, 'session_id': session_id, 'mode': 'document', 'message_type': 'answer', 'metadata': {'processing_time_ms': processing_time_ms, 'chunks_retrieved': result['metadata'].get('chunks_retrieved', 0)}})}\n\n"
                
                # CASE 3: Standard Streaming Chat
                else:
                    # Stream chunks from AI service
                    async for chunk in ai_service.generate_response_stream(agent_id, message):
                        yield f"data: {json.dumps({'chunk': chunk})}\n\n"
                    
                    # Calculate processing time
                    processing_time_ms = int((time.time() - start_time) * 1000)
                    
                    # Send completion event
                    yield f"data: {json.dumps({'done': True, 'mode': 'general', 'message_type': 'text', 'metadata': {'processing_time_ms': processing_time_ms}})}\n\n"
                    
                    logger.info(f"Successfully completed streaming response for agent '{agent_id}' in {processing_time_ms}ms")
                
            except asyncio.TimeoutError as e:
                # Send timeout error
                yield f"data: {json.dumps({'error': str(e), 'code': 504})}\n\n"
                logger.warning(f"Request timeout for agent '{agent_id}': {e}")
                
            except Exception as e:
                # Send error event
                yield f"data: {json.dumps({'error': 'AI service temporarily unavailable', 'code': 500})}\n\n"
                logger.error(f"Error in streaming response for agent '{agent_id}': {e}", exc_info=True)
        
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
        logger.error(f"Error setting up streaming for agent '{agent_id}': {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="AI service temporarily unavailable. Please try again later."
        )
