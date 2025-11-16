"""
Embedding service for generating vector embeddings from text.
Uses sentence-transformers for efficient embedding generation.
"""

import logging
from typing import List
import asyncio
from concurrent.futures import ThreadPoolExecutor
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating text embeddings."""
    
    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        max_workers: int = 4
    ):
        """Initialize embedding service.
        
        Args:
            model_name: Name of the sentence-transformers model
            max_workers: Number of worker threads for embedding generation
        """
        self.model_name = model_name
        self.executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="embedding"
        )
        
        # Load model (this is blocking, but only happens once)
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        logger.info(f"Embedding model loaded: {model_name}")
    
    def __del__(self):
        """Cleanup executor on service destruction."""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts asynchronously.
        
        Args:
            texts: List of text strings to embed
        
        Returns:
            List of embedding vectors (each is a list of floats)
        
        Raises:
            ValueError: If texts is empty or invalid
        """
        if not texts:
            raise ValueError("Cannot embed empty text list")
        
        logger.debug(f"Generating embeddings for {len(texts)} texts")
        
        # Run embedding generation in executor (blocking operation)
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            self.executor,
            self._sync_embed,
            texts
        )
        
        logger.debug(f"Generated {len(embeddings)} embeddings")
        
        return embeddings
    
    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text asynchronously.
        
        Args:
            text: Text string to embed
        
        Returns:
            Embedding vector as list of floats
        
        Raises:
            ValueError: If text is empty
        """
        if not text or not text.strip():
            raise ValueError("Cannot embed empty text")
        
        embeddings = await self.embed_texts([text])
        return embeddings[0]
    
    def _sync_embed(self, texts: List[str]) -> List[List[float]]:
        """Synchronous embedding generation (runs in executor).
        
        Args:
            texts: List of text strings
        
        Returns:
            List of embedding vectors
        """
        # Generate embeddings (blocking call)
        embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
            show_progress_bar=False
        )
        
        # Convert numpy arrays to lists
        return [emb.tolist() for emb in embeddings]
    
    @property
    def embedding_dimension(self) -> int:
        """Get the dimension of the embedding vectors.
        
        Returns:
            Embedding dimension
        """
        return self.model.get_sentence_embedding_dimension()
