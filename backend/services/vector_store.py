"""
In-memory vector store using FAISS for similarity search.
All data is kept in RAM and can be explicitly deleted.
"""

import logging
from typing import List, Dict, Any, Tuple
import numpy as np
import faiss

logger = logging.getLogger(__name__)


class VectorStore:
    """In-memory vector store for similarity search."""
    
    def __init__(self, dimension: int):
        """Initialize vector store.
        
        Args:
            dimension: Dimension of the embedding vectors
        """
        self.dimension = dimension
        
        # Create FAISS index (L2 distance)
        self.index = faiss.IndexFlatL2(dimension)
        
        # Store metadata for each vector
        self.metadata: List[Dict[str, Any]] = []
        
        logger.debug(f"VectorStore initialized with dimension {dimension}")
    
    def add_vectors(
        self,
        vectors: List[List[float]],
        metadata: List[Dict[str, Any]]
    ) -> None:
        """Add vectors to the store with associated metadata.
        
        Args:
            vectors: List of embedding vectors
            metadata: List of metadata dicts (one per vector)
        
        Raises:
            ValueError: If vectors and metadata lengths don't match
        """
        if len(vectors) != len(metadata):
            raise ValueError(
                f"Vectors ({len(vectors)}) and metadata ({len(metadata)}) "
                "lengths must match"
            )
        
        if not vectors:
            return
        
        # Convert to numpy array
        vectors_np = np.array(vectors, dtype=np.float32)
        
        # Add to FAISS index
        self.index.add(vectors_np)
        
        # Store metadata
        self.metadata.extend(metadata)
        
        logger.debug(f"Added {len(vectors)} vectors to store")
    
    def search(
        self,
        query_vector: List[float],
        top_k: int = 5
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Search for similar vectors.
        
        Args:
            query_vector: Query embedding vector
            top_k: Number of results to return
        
        Returns:
            List of (metadata, distance) tuples, sorted by similarity
        """
        if self.index.ntotal == 0:
            logger.warning("Search called on empty vector store")
            return []
        
        # Limit top_k to available vectors
        top_k = min(top_k, self.index.ntotal)
        
        # Convert query to numpy array
        query_np = np.array([query_vector], dtype=np.float32)
        
        # Search FAISS index
        distances, indices = self.index.search(query_np, top_k)
        
        # Build results with metadata
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx < len(self.metadata):
                results.append((self.metadata[idx], float(distance)))
        
        logger.debug(f"Search returned {len(results)} results")
        
        return results
    
    def clear(self) -> None:
        """Clear all vectors and metadata from the store."""
        # Reset FAISS index
        self.index.reset()
        
        # Clear metadata
        self.metadata.clear()
        
        logger.debug("VectorStore cleared")
    
    def size(self) -> int:
        """Get the number of vectors in the store.
        
        Returns:
            Number of vectors
        """
        return self.index.ntotal
