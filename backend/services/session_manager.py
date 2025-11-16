"""
Session manager for ephemeral document contexts.
Manages in-memory sessions with TTL and explicit cleanup.
"""

import asyncio
import logging
import secrets
import time
import gc
from typing import Dict, Optional, Any
from dataclasses import dataclass, field

from backend.services.vector_store import VectorStore
from backend.services.document_processor import DocumentChunk

logger = logging.getLogger(__name__)


@dataclass
class SessionContext:
    """Ephemeral session context for document RAG."""
    
    session_id: str
    vector_store: VectorStore
    chunks: list[DocumentChunk]
    created_at: float
    expires_at: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    image_data: Optional[bytes] = None  # Store original image for vision queries
    
    def is_expired(self) -> bool:
        """Check if session has expired.
        
        Returns:
            True if expired, False otherwise
        """
        return time.time() > self.expires_at


class SessionManager:
    """Manager for ephemeral document sessions."""
    
    def __init__(self, default_ttl_minutes: int = 20):
        """Initialize session manager.
        
        Args:
            default_ttl_minutes: Default session TTL in minutes
        """
        self.default_ttl_minutes = default_ttl_minutes
        self.sessions: Dict[str, SessionContext] = {}
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False
        
        logger.info(
            f"SessionManager initialized (default_ttl={default_ttl_minutes}min)"
        )
    
    async def start(self) -> None:
        """Start the session manager and cleanup task."""
        if self._running:
            return
        
        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("SessionManager started")
    
    async def stop(self) -> None:
        """Stop the session manager and cleanup task."""
        self._running = False
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Clear all sessions
        await self.clear_all()
        
        logger.info("SessionManager stopped")
    
    def create_session(
        self,
        vector_store: VectorStore,
        chunks: list[DocumentChunk],
        metadata: Dict[str, Any] = None,
        ttl_minutes: Optional[int] = None,
        image_data: Optional[bytes] = None
    ) -> str:
        """Create a new ephemeral session.
        
        Args:
            vector_store: Vector store with document embeddings
            chunks: List of document chunks
            metadata: Optional session metadata
            ttl_minutes: Optional custom TTL (uses default if not provided)
            image_data: Optional original image data for vision queries
        
        Returns:
            Session ID
        """
        # Generate cryptographically random session ID
        session_id = f"s_{secrets.token_urlsafe(16)}"
        
        # Calculate expiry time
        ttl = ttl_minutes if ttl_minutes is not None else self.default_ttl_minutes
        created_at = time.time()
        expires_at = created_at + (ttl * 60)
        
        # Create session context
        context = SessionContext(
            session_id=session_id,
            vector_store=vector_store,
            chunks=chunks,
            created_at=created_at,
            expires_at=expires_at,
            metadata=metadata or {},
            image_data=image_data
        )
        
        # Store session
        self.sessions[session_id] = context
        
        logger.info(
            f"Created session {session_id} (ttl={ttl}min, "
            f"chunks={len(chunks)}, vectors={vector_store.size()}, "
            f"image_data={'present' if image_data else 'none'})"
        )
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[SessionContext]:
        """Get a session by ID.
        
        Args:
            session_id: Session ID
        
        Returns:
            SessionContext if found and not expired, None otherwise
        """
        context = self.sessions.get(session_id)
        
        if context is None:
            logger.debug(f"Session {session_id} not found")
            return None
        
        if context.is_expired():
            logger.info(f"Session {session_id} expired, removing")
            asyncio.create_task(self.delete_session(session_id))
            return None
        
        return context
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete a session and free its resources.
        
        Args:
            session_id: Session ID
        
        Returns:
            True if deleted, False if not found
        """
        context = self.sessions.pop(session_id, None)
        
        if context is None:
            logger.debug(f"Session {session_id} not found for deletion")
            return False
        
        # Clear vector store
        context.vector_store.clear()
        
        # Clear chunks
        context.chunks.clear()
        
        # Clear metadata
        context.metadata.clear()
        
        # Explicitly delete references
        del context.vector_store
        del context.chunks
        del context.metadata
        del context
        
        # Force garbage collection
        gc.collect()
        
        logger.info(f"Deleted session {session_id}")
        
        return True
    
    async def clear_all(self) -> int:
        """Clear all sessions.
        
        Returns:
            Number of sessions cleared
        """
        session_ids = list(self.sessions.keys())
        
        for session_id in session_ids:
            await self.delete_session(session_id)
        
        logger.info(f"Cleared all {len(session_ids)} sessions")
        
        return len(session_ids)
    
    def get_active_session_count(self) -> int:
        """Get the number of active sessions.
        
        Returns:
            Number of active sessions
        """
        return len(self.sessions)
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a session.
        
        Args:
            session_id: Session ID
        
        Returns:
            Session info dict or None if not found
        """
        context = self.get_session(session_id)
        
        if context is None:
            return None
        
        return {
            "session_id": context.session_id,
            "created_at": context.created_at,
            "expires_at": context.expires_at,
            "ttl_remaining_seconds": int(context.expires_at - time.time()),
            "chunk_count": len(context.chunks),
            "vector_count": context.vector_store.size(),
            "metadata": context.metadata
        }
    
    async def _cleanup_loop(self) -> None:
        """Background task to cleanup expired sessions."""
        logger.info("Session cleanup loop started")
        
        while self._running:
            try:
                # Wait 60 seconds between cleanup runs
                await asyncio.sleep(60)
                
                # Find expired sessions
                current_time = time.time()
                expired_sessions = [
                    session_id
                    for session_id, context in self.sessions.items()
                    if context.is_expired()
                ]
                
                # Delete expired sessions
                for session_id in expired_sessions:
                    await self.delete_session(session_id)
                
                if expired_sessions:
                    logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}", exc_info=True)
        
        logger.info("Session cleanup loop stopped")
