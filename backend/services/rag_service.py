"""
RAG (Retrieval-Augmented Generation) service for document Q&A.
Orchestrates document processing, embedding, retrieval, and generation.
"""

import asyncio
import logging
from typing import List, Dict, Any, Tuple
import google.generativeai as genai

from backend.services.document_processor import DocumentProcessor, DocumentChunk
from backend.services.embedding_service import EmbeddingService
from backend.services.vector_store import VectorStore
from backend.services.session_manager import SessionManager
from backend.config import Settings

logger = logging.getLogger(__name__)


class RAGService:
    """Service for document-based RAG operations."""
    
    def __init__(
        self,
        settings: Settings,
        session_manager: SessionManager,
        embedding_service: EmbeddingService,
        document_processor: DocumentProcessor
    ):
        """Initialize RAG service.
        
        Args:
            settings: Application settings
            session_manager: Session manager for ephemeral contexts
            embedding_service: Service for generating embeddings
            document_processor: Service for processing documents
        """
        self.settings = settings
        self.session_manager = session_manager
        self.embedding_service = embedding_service
        self.document_processor = document_processor
        
        # Configure Gemini for vision
        genai.configure(api_key=settings.gemini_api_key)
        self.vision_model = genai.GenerativeModel('gemini-2.0-flash')
        self.text_model = genai.GenerativeModel(
            'gemini-2.0-flash',
            generation_config={
                'temperature': 0.7,
                'top_p': 0.95,
                'max_output_tokens': 2048,
            }
        )
        
        logger.info("RAGService initialized")
    
    async def process_pdf(
        self,
        file_bytes: bytes,
        timeout: int = 30
    ) -> str:
        """Process a PDF file and create an ephemeral session.
        
        Args:
            file_bytes: PDF file content
            timeout: Processing timeout in seconds
        
        Returns:
            Session ID
        
        Raises:
            asyncio.TimeoutError: If processing exceeds timeout
            ValueError: If PDF processing fails
        """
        try:
            return await asyncio.wait_for(
                self._process_pdf_internal(file_bytes),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            logger.error("PDF processing timed out")
            raise asyncio.TimeoutError(
                f"PDF processing timed out after {timeout} seconds"
            )
    
    async def process_image(
        self,
        file_bytes: bytes,
        timeout: int = 20
    ) -> str:
        """Process an image file and create an ephemeral session.
        
        Args:
            file_bytes: Image file content
            timeout: Processing timeout in seconds
        
        Returns:
            Session ID
        
        Raises:
            asyncio.TimeoutError: If processing exceeds timeout
            ValueError: If image processing fails
        """
        try:
            return await asyncio.wait_for(
                self._process_image_internal(file_bytes),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            logger.error("Image processing timed out")
            raise asyncio.TimeoutError(
                f"Image processing timed out after {timeout} seconds"
            )
    
    async def query_session(
        self,
        session_id: str,
        query: str,
        top_k: int = 5,
        timeout: int = 15
    ) -> Dict[str, Any]:
        """Query a document session.
        
        Args:
            session_id: Session ID
            query: User query
            top_k: Number of chunks to retrieve
            timeout: Query timeout in seconds
        
        Returns:
            Dict with reply, source_chunks, and metadata
        
        Raises:
            ValueError: If session not found
            asyncio.TimeoutError: If query exceeds timeout
        """
        try:
            return await asyncio.wait_for(
                self._query_session_internal(session_id, query, top_k),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            logger.error(f"Query timed out for session {session_id}")
            raise asyncio.TimeoutError(
                f"Query timed out after {timeout} seconds"
            )
    
    async def _process_pdf_internal(self, file_bytes: bytes) -> str:
        """Internal PDF processing logic."""
        logger.info("Processing PDF document")
        
        # Extract text and images from PDF
        chunks, images = await self.document_processor.process_pdf(file_bytes)
        
        if not chunks and not images:
            raise ValueError("No content extracted from PDF")
        
        # Process images with vision model
        image_descriptions = []
        if images:
            logger.info(f"Processing {len(images)} images with vision model")
            image_descriptions = await self._process_images_with_vision(images)
        
        # Combine text chunks with image descriptions
        all_chunks = chunks.copy()
        for desc, page_num in image_descriptions:
            # Create a chunk for each image description
            chunk = DocumentChunk(
                text=f"[Image Description] {desc}",
                page=page_num,
                chunk_id=len(all_chunks),
                metadata={"type": "image_description"}
            )
            all_chunks.append(chunk)
        
        # Generate embeddings for all chunks
        chunk_texts = [chunk.text for chunk in all_chunks]
        embeddings = await self.embedding_service.embed_texts(chunk_texts)
        
        # Create vector store
        vector_store = VectorStore(self.embedding_service.embedding_dimension)
        
        # Prepare metadata for vector store
        metadata_list = [
            {
                "text": chunk.text,
                "page": chunk.page,
                "chunk_id": chunk.chunk_id,
                "type": chunk.metadata.get("type", "text")
            }
            for chunk in all_chunks
        ]
        
        # Add vectors to store
        vector_store.add_vectors(embeddings, metadata_list)
        
        # Create session
        session_id = self.session_manager.create_session(
            vector_store=vector_store,
            chunks=all_chunks,
            metadata={
                "document_type": "pdf",
                "text_chunks": len(chunks),
                "image_chunks": len(image_descriptions),
                "total_chunks": len(all_chunks)
            }
        )
        
        logger.info(
            f"PDF processed successfully: session={session_id}, "
            f"chunks={len(all_chunks)}"
        )
        
        return session_id
    
    async def _process_image_internal(self, file_bytes: bytes) -> str:
        """Internal image processing logic."""
        logger.info("Processing image document")
        
        # Validate and process image
        image_bytes, metadata = await self.document_processor.process_image(
            file_bytes
        )
        
        # Get image description from vision model for initial context
        description = await self._get_image_description(image_bytes)
        
        # Create a single chunk with the description
        chunk = DocumentChunk(
            text=f"[Image Content] {description}",
            page=1,
            chunk_id=0,
            metadata={"type": "image_description", "image_metadata": metadata}
        )
        
        # Generate embedding
        embeddings = await self.embedding_service.embed_texts([chunk.text])
        
        # Create vector store
        vector_store = VectorStore(self.embedding_service.embedding_dimension)
        
        # Add vector to store
        vector_store.add_vectors(
            embeddings,
            [{
                "text": chunk.text,
                "page": 1,
                "chunk_id": 0,
                "type": "image_description"
            }]
        )
        
        # Create session WITH original image data for vision queries
        session_id = self.session_manager.create_session(
            vector_store=vector_store,
            chunks=[chunk],
            metadata={
                "document_type": "image",
                "image_format": metadata.get("format"),
                "image_size": metadata.get("size")
            },
            image_data=image_bytes  # Store original image
        )
        
        logger.info(f"Image processed successfully: session={session_id}")
        
        return session_id
    
    async def _query_session_internal(
        self,
        session_id: str,
        query: str,
        top_k: int
    ) -> Dict[str, Any]:
        """Internal query logic."""
        # Get session
        context = self.session_manager.get_session(session_id)
        if context is None:
            raise ValueError(f"Session {session_id} not found or expired")
        
        logger.info(f"Querying session {session_id}: {query[:50]}...")
        
        # Check if this is an image session - use vision model directly
        if context.image_data is not None:
            logger.info("Using vision model for image query")
            result = await self._query_image_with_vision(context.image_data, query)
            
            # If None is returned, it means the query is general (not about the image)
            if result is None:
                logger.info("Query is general knowledge, not about the image")
                # Return a special marker to signal fallback to general agent
                return {
                    "reply": None,  # Signal for general mode
                    "source_chunks": [],
                    "metadata": {"fallback_to_general": True}
                }
            
            return result
        
        # For PDF/text documents, use traditional RAG
        # Generate query embedding
        query_embedding = await self.embedding_service.embed_text(query)
        
        # Search vector store
        results = context.vector_store.search(query_embedding, top_k)
        
        if not results:
            return {
                "reply": "I couldn't find relevant information in the document to answer your question.",
                "source_chunks": [],
                "metadata": {"chunks_retrieved": 0}
            }
        
        # Build context from retrieved chunks
        context_parts = []
        source_chunks = []
        
        for metadata, distance in results:
            context_parts.append(
                f"[Page {metadata['page']}] {metadata['text']}"
            )
            source_chunks.append({
                "page": metadata["page"],
                "excerpt": metadata["text"][:200] + "..." if len(metadata["text"]) > 200 else metadata["text"],
                "type": metadata.get("type", "text")
            })
        
        # Build RAG prompt
        context_text = "\n\n".join(context_parts)
        prompt = self._build_rag_prompt(context_text, query)
        
        # Generate response
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            self._sync_generate,
            prompt
        )
        
        # Check if the AI determined this is a general query
        if "GENERAL_QUERY" in response.strip():
            logger.info("RAG detected general query for PDF, signaling fallback")
            return {
                "reply": None,  # Signal for general mode
                "source_chunks": [],
                "metadata": {"fallback_to_general": True}
            }
        
        logger.info(f"Generated response for session {session_id}")
        
        return {
            "reply": response,
            "source_chunks": source_chunks,
            "metadata": {
                "chunks_retrieved": len(results),
                "model": "gemini-2.0-flash"
            }
        }
    
    async def _process_images_with_vision(
        self,
        images: List[Tuple[bytes, int]]
    ) -> List[Tuple[str, int]]:
        """Process images with vision model to get descriptions.
        
        Args:
            images: List of (image_bytes, page_num) tuples
        
        Returns:
            List of (description, page_num) tuples
        """
        descriptions = []
        
        for image_bytes, page_num in images:
            try:
                description = await self._get_image_description(image_bytes)
                descriptions.append((description, page_num))
            except Exception as e:
                logger.warning(
                    f"Failed to process image from page {page_num}: {e}"
                )
                # Add placeholder description
                descriptions.append(
                    (f"[Image on page {page_num} - processing failed]", page_num)
                )
        
        return descriptions
    
    async def _get_image_description(self, image_bytes: bytes) -> str:
        """Get description of an image using vision model.
        
        Args:
            image_bytes: Image content as bytes
        
        Returns:
            Image description
        """
        from PIL import Image
        import io
        
        # Load image
        image = Image.open(io.BytesIO(image_bytes))
        
        # Create prompt for vision model
        prompt = (
            "Describe this image in detail. Include any text, diagrams, "
            "charts, tables, or important visual elements. Be specific and "
            "comprehensive."
        )
        
        # Generate description (blocking call)
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            self._sync_vision_generate,
            prompt,
            image
        )
        
        return response
    
    def _sync_vision_generate(self, prompt: str, image) -> str:
        """Synchronous vision model generation."""
        response = self.vision_model.generate_content([prompt, image])
        return response.text.strip()
    
    def _sync_generate(self, prompt: str) -> str:
        """Synchronous text generation."""
        response = self.text_model.generate_content(prompt)
        return response.text.strip()
    
    async def _query_image_with_vision(
        self,
        image_bytes: bytes,
        query: str
    ) -> Dict[str, Any]:
        """Query an image directly using vision model with intelligent context detection.
        
        This method intelligently determines if the query is about the uploaded image
        or a general knowledge question, and responds accordingly.
        
        Args:
            image_bytes: Original image data
            query: User query
        
        Returns:
            Dict with reply and metadata, or None if query is not about the image
        """
        from PIL import Image
        import io
        
        # Load image
        image = Image.open(io.BytesIO(image_bytes))
        
        # Build vision prompt that can handle both document and general queries
        prompt = f"""You are a helpful AI tutor. The user has uploaded an image and is asking you a question.

User Question: {query}

IMPORTANT: First, determine if this question is:
A) About the content IN THE IMAGE (solve this, what's in the image, explain this diagram, etc.)
B) A GENERAL knowledge question (what is calculus, explain photosynthesis, etc.)

If it's TYPE A (about the image):
- Look at the image and answer based on what you see
- Use the formatting structure below

If it's TYPE B (general knowledge):
- Respond with exactly: "GENERAL_QUERY"
- Do not answer the question
- Just return those two words

---

FORMATTING FOR IMAGE-BASED ANSWERS:

CRITICAL FORMATTING RULES:
- Use clear headings with ## for main sections
- Use **bold** for step numbers and key terms
- Add blank lines between steps for readability
- Use bullet points (-) for sub-items
- Use code blocks for mathematical expressions when helpful

SOLUTION STRUCTURE FOR MATH PROBLEMS:

## Problem
[State what needs to be solved]

## Given Information
[List known values and conditions]

## Solution

**Step 1: [Step name]**
[Explanation]
[Calculation if any]

**Step 2: [Step name]**
[Explanation]
[Calculation if any]

[Continue for all steps...]

## Final Answer
[Clear statement of the answer]

---

SOLUTION STRUCTURE FOR ENGLISH QUESTIONS:

## Question
[State what is being asked]

## Analysis

**Step 1: [Identify/Understand]**
[Your analysis]

**Step 2: [Examine/Evaluate]**
[Your reasoning]

**Step 3: [Conclude]**
[Your conclusion]

## Answer
[Clear final answer]

---

SOLUTION STRUCTURE FOR SCIENCE (Physics/Chemistry):

## Problem
[State the problem]

## Given
- [List all given values with units]

## Concept
[State relevant principles/formulas]

## Solution

**Step 1: [Step name]**
[Explanation and calculation]

**Step 2: [Step name]**
[Explanation and calculation]

[Continue...]

## Final Answer
[Answer with proper units]

---

Now, first determine if this is TYPE A or TYPE B. If TYPE B, respond with "GENERAL_QUERY". If TYPE A, answer using the appropriate structure above.

Answer:"""
        
        # Generate response using vision model
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            self._sync_vision_generate,
            prompt,
            image
        )
        
        # Check if the AI determined this is a general query
        if "GENERAL_QUERY" in response.strip():
            logger.info("Vision model detected general query, signaling fallback")
            return None  # Signal to use general agent mode
        
        logger.info("Generated vision-based response for image query")
        
        return {
            "reply": response,
            "source_chunks": [{
                "page": 1,
                "excerpt": "[Image content analyzed using vision model]",
                "type": "image_vision"
            }],
            "metadata": {
                "chunks_retrieved": 1,
                "model": "gemini-2.0-flash-vision",
                "query_type": "vision"
            }
        }
    
    def _build_rag_prompt(self, context: str, query: str) -> str:
        """Build RAG prompt with context and query, with intelligent fallback detection.
        
        Args:
            context: Retrieved context from document
            query: User query
        
        Returns:
            Complete prompt
        """
        prompt = f"""You are a helpful assistant that answers questions based on the provided document context.

Document Context:
{context}

User Question: {query}

IMPORTANT: First, determine if this question is:
A) About the content IN THE DOCUMENT (specific questions about what's written, problems to solve from the document, etc.)
B) A GENERAL knowledge question that's NOT about this specific document (definitions, concepts, general explanations)

If it's TYPE B (general knowledge not in document):
- Respond with exactly: "GENERAL_QUERY"
- Do not answer the question
- Just return those two words

If it's TYPE A (about the document):
- Answer based ONLY on the information provided in the document context above
- If the context doesn't contain enough information, say so clearly
- Be specific and cite relevant parts of the document when possible
- If the context mentions page numbers, include them in your answer
- Keep your answer concise but complete

Answer:"""
        
        return prompt
