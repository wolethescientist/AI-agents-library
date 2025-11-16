"""
Documents API router for ephemeral multi-modal RAG endpoints.
Handles PDF and image uploads with in-memory processing.
"""

import asyncio
import logging
import time
from datetime import datetime
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from typing import Annotated

from backend.models.requests import DocumentQueryRequest
from backend.models.responses import SuccessResponse
from backend.services.rag_service import RAGService

logger = logging.getLogger(__name__)

# Create router with prefix and tags
router = APIRouter(prefix="/api/v1/documents", tags=["documents"])

# Service dependency
_rag_service: RAGService = None


def set_rag_service(rag_service: RAGService):
    """Set the RAG service instance for dependency injection.
    
    Args:
        rag_service: The RAGService instance
    """
    global _rag_service
    _rag_service = rag_service
    logger.info("Documents router RAG service initialized")


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


# Configuration constants
MAX_FILE_SIZE = 30 * 1024 * 1024  # 30 MB
ALLOWED_PDF_TYPES = ["application/pdf"]
ALLOWED_IMAGE_TYPES = [
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/heic"
]
SESSION_TTL_MINUTES = 20


@router.post(
    "",
    response_model=SuccessResponse,
    summary="Upload document for ephemeral RAG",
    description="Upload a PDF or image file to create an in-memory RAG context",
    responses={
        200: {
            "description": "Document processed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": {
                            "session_id": "s_Ab3xYz...",
                            "expires_in_minutes": 20
                        },
                        "message": "Document processed in memory. It will be available for 20 minutes.",
                        "privacy": "Uploaded file and derived data are not saved to disk or DB and will be removed after expiry."
                    }
                }
            }
        },
        400: {
            "description": "Invalid file or request"
        },
        413: {
            "description": "File too large"
        },
        422: {
            "description": "Unsupported file type"
        },
        500: {
            "description": "Processing error"
        },
        504: {
            "description": "Processing timeout"
        }
    }
)
async def upload_document(
    file: Annotated[UploadFile, File(description="PDF or image file to process")],
    rag_service: Annotated[RAGService, Depends(get_rag_service)]
) -> SuccessResponse:
    """Upload a document (PDF or image) for ephemeral RAG processing.
    
    This endpoint:
    - Accepts PDF or image files (PNG, JPG, JPEG, HEIC)
    - Processes the file entirely in memory (no disk writes)
    - Extracts text and images from PDFs
    - Uses vision AI to understand images
    - Creates searchable embeddings
    - Returns a session ID for querying
    - Automatically expires after 20 minutes
    
    **File Requirements:**
    - Maximum size: 30 MB
    - Supported formats: PDF, PNG, JPG, JPEG, HEIC
    
    **Privacy Guarantee:**
    All uploaded data is processed in RAM only and never written to disk or database.
    Data is automatically deleted after the session expires or when explicitly deleted.
    
    **Example Request:**
    ```bash
    curl -X POST "http://localhost:8000/api/v1/documents" \\
         -F "file=@document.pdf"
    ```
    
    Args:
        file: Uploaded file (multipart/form-data)
        rag_service: Injected RAGService dependency
    
    Returns:
        SuccessResponse with session_id and expiry information
    
    Raises:
        HTTPException: 400/413/422/500/504 for various errors
    """
    start_time = time.time()
    
    logger.info(
        f"Document upload request: filename={file.filename}, "
        f"content_type={file.content_type}"
    )
    
    try:
        # Validate content type
        if file.content_type not in ALLOWED_PDF_TYPES + ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=422,
                detail=f"Unsupported file type '{file.content_type}'. "
                       f"Supported types: PDF, PNG, JPG, JPEG, HEIC. "
                       f"Ensure your file has the correct MIME type and extension."
            )
        
        # Read file content (in memory)
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
            session_id = await rag_service.process_pdf(file_bytes)
        else:
            session_id = await rag_service.process_image(file_bytes)
        
        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        logger.info(
            f"Document processed successfully: session={session_id}, "
            f"time={processing_time_ms}ms"
        )
        
        return SuccessResponse(
            success=True,
            data={
                "session_id": session_id,
                "expires_in_minutes": SESSION_TTL_MINUTES,
                "processing_time_ms": processing_time_ms
            },
            message=f"Document processed in memory. It will be available for {SESSION_TTL_MINUTES} minutes.",
            privacy="Uploaded file and derived data are not saved to disk or DB and will be removed after expiry."
        )
    
    except HTTPException:
        raise
    
    except asyncio.TimeoutError as e:
        logger.error(f"Document processing timeout: {e}")
        raise HTTPException(
            status_code=504,
            detail=str(e)
        )
    
    except ValueError as e:
        logger.error(f"Document processing error: {e}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    
    except Exception as e:
        logger.error(f"Unexpected error processing document: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to process document. Please try again."
        )


@router.post(
    "/sessions/{session_id}/query",
    response_model=SuccessResponse,
    summary="Query a document session",
    description="Ask questions about an uploaded document using its session ID",
    responses={
        200: {
            "description": "Query answered successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": {
                            "agent": "document",
                            "reply": "The diagram shows oxygen evolution from electrolysis...",
                            "source_chunks": [
                                {
                                    "page": 3,
                                    "excerpt": "During electrolysis, oxygen forms at the anode...",
                                    "type": "text"
                                }
                            ],
                            "model_info": {
                                "model": "gemini-2.0-flash",
                                "latency_ms": 4200
                            },
                            "timestamp": "2025-11-09T20:34:00Z"
                        },
                        "message": "Answer generated from uploaded document context."
                    }
                }
            }
        },
        404: {
            "description": "Session not found or expired"
        },
        400: {
            "description": "Invalid query"
        },
        504: {
            "description": "Query timeout"
        },
        500: {
            "description": "Query processing error"
        }
    }
)
async def query_document(
    session_id: str,
    request: DocumentQueryRequest,
    rag_service: Annotated[RAGService, Depends(get_rag_service)]
) -> SuccessResponse:
    """Query a document using its session ID.
    
    This endpoint:
    - Retrieves relevant chunks from the document using semantic search
    - Generates an answer based on the retrieved context
    - Returns source citations with page numbers
    - Includes metadata about the retrieval and generation process
    
    **Example Request:**
    ```bash
    curl -X POST "http://localhost:8000/api/v1/documents/sessions/s_Ab3xYz.../query" \\
         -H "Content-Type: application/json" \\
         -d '{"message": "What are the main findings?"}'
    ```
    
    Args:
        session_id: Session ID from document upload
        request: Query request with user message
        rag_service: Injected RAGService dependency
    
    Returns:
        SuccessResponse with answer, source chunks, and metadata
    
    Raises:
        HTTPException: 404/400/504/500 for various errors
    """
    start_time = time.time()
    
    logger.info(f"Query request for session {session_id}: {request.message[:50]}...")
    
    try:
        # Query the session
        result = await rag_service.query_session(
            session_id=session_id,
            query=request.message,
            top_k=5
        )
        
        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        # Build response
        response_data = {
            "agent": "document",
            "reply": result["reply"],
            "source_chunks": result["source_chunks"],
            "model_info": {
                "model": result["metadata"].get("model", "gemini-2.0-flash"),
                "latency_ms": processing_time_ms,
                "chunks_retrieved": result["metadata"].get("chunks_retrieved", 0)
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        logger.info(
            f"Query answered successfully: session={session_id}, "
            f"time={processing_time_ms}ms"
        )
        
        return SuccessResponse(
            success=True,
            data=response_data,
            message="Answer generated from uploaded document context."
        )
    
    except ValueError as e:
        logger.warning(f"Session not found: {e}")
        raise HTTPException(
            status_code=404,
            detail=f"{str(e)}. Sessions expire after 20 minutes of inactivity. "
                   f"Upload a new document to create a new session."
        )
    
    except asyncio.TimeoutError as e:
        logger.error(f"Query timeout: {e}")
        raise HTTPException(
            status_code=504,
            detail=str(e)
        )
    
    except Exception as e:
        logger.error(f"Error processing query: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to process query. Please try again."
        )


@router.delete(
    "/sessions/{session_id}",
    response_model=SuccessResponse,
    summary="Delete a document session",
    description="Explicitly delete a session and free its resources",
    responses={
        200: {
            "description": "Session deleted successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": {
                            "session_id": "s_Ab3xYz...",
                            "deleted": True
                        },
                        "message": "Session deleted successfully. All data has been removed from memory."
                    }
                }
            }
        },
        404: {
            "description": "Session not found"
        }
    }
)
async def delete_session(
    session_id: str,
    rag_service: Annotated[RAGService, Depends(get_rag_service)]
) -> SuccessResponse:
    """Delete a document session and free its resources.
    
    This endpoint:
    - Immediately removes all session data from memory
    - Clears embeddings and vector indices
    - Frees all associated resources
    - Triggers garbage collection
    
    Sessions are automatically deleted after expiry, but this endpoint
    allows explicit cleanup when the document is no longer needed.
    
    **Example Request:**
    ```bash
    curl -X DELETE "http://localhost:8000/api/v1/documents/sessions/s_Ab3xYz..."
    ```
    
    Args:
        session_id: Session ID to delete
        rag_service: Injected RAGService dependency
    
    Returns:
        SuccessResponse confirming deletion
    
    Raises:
        HTTPException: 404 if session not found
    """
    logger.info(f"Delete request for session {session_id}")
    
    try:
        # Delete the session
        deleted = await rag_service.session_manager.delete_session(session_id)
        
        if not deleted:
            raise HTTPException(
                status_code=404,
                detail=f"Session '{session_id}' not found. It may have already been deleted or expired."
            )
        
        logger.info(f"Session {session_id} deleted successfully")
        
        return SuccessResponse(
            success=True,
            data={
                "session_id": session_id,
                "deleted": True
            },
            message="Session deleted successfully. All data has been removed from memory."
        )
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Error deleting session: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to delete session. Please try again."
        )
