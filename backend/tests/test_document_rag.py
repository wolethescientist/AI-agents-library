"""
Integration tests for ephemeral multi-modal RAG system.
Tests document upload, processing, querying, and session management.
"""

import pytest
import asyncio
import io
from PIL import Image
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock

from backend.main import create_app
from backend.services.document_processor import DocumentProcessor, DocumentChunk
from backend.services.embedding_service import EmbeddingService
from backend.services.vector_store import VectorStore
from backend.services.session_manager import SessionManager


@pytest.fixture
def test_app():
    """Create test application."""
    app = create_app()
    return app


@pytest.fixture
def client(test_app):
    """Create test client."""
    return TestClient(test_app)


@pytest.fixture
def document_processor():
    """Create document processor instance."""
    return DocumentProcessor(chunk_size=100, chunk_overlap=20)


@pytest.fixture
async def session_manager():
    """Create session manager instance."""
    manager = SessionManager(default_ttl_minutes=1)
    await manager.start()
    yield manager
    await manager.stop()


@pytest.fixture
def sample_pdf_bytes():
    """Create a simple PDF for testing."""
    import fitz
    
    # Create a simple PDF in memory
    pdf = fitz.open()
    page = pdf.new_page()
    page.insert_text((50, 50), "This is a test document about machine learning.")
    page.insert_text((50, 100), "Neural networks are powerful tools for AI.")
    
    # Convert to bytes
    pdf_bytes = pdf.tobytes()
    pdf.close()
    
    return pdf_bytes


@pytest.fixture
def sample_image_bytes():
    """Create a simple image for testing."""
    # Create a simple test image
    img = Image.new('RGB', (100, 100), color='red')
    
    # Convert to bytes
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    return img_bytes.getvalue()


class TestDocumentProcessor:
    """Test document processing functionality."""
    
    @pytest.mark.asyncio
    async def test_process_pdf(self, document_processor, sample_pdf_bytes):
        """Test PDF processing extracts text and creates chunks."""
        chunks, images = await document_processor.process_pdf(sample_pdf_bytes)
        
        assert len(chunks) > 0, "Should extract at least one chunk"
        assert isinstance(chunks[0], DocumentChunk)
        assert chunks[0].text, "Chunk should have text"
        assert chunks[0].page > 0, "Chunk should have page number"
    
    @pytest.mark.asyncio
    async def test_process_image(self, document_processor, sample_image_bytes):
        """Test image processing validates and processes image."""
        image_bytes, metadata = await document_processor.process_image(sample_image_bytes)
        
        assert image_bytes, "Should return processed image bytes"
        assert metadata["format"] == "PNG"
        assert metadata["width"] > 0
        assert metadata["height"] > 0
    
    @pytest.mark.asyncio
    async def test_process_invalid_pdf(self, document_processor):
        """Test processing invalid PDF raises error."""
        with pytest.raises(ValueError):
            await document_processor.process_pdf(b"invalid pdf content")
    
    @pytest.mark.asyncio
    async def test_process_invalid_image(self, document_processor):
        """Test processing invalid image raises error."""
        with pytest.raises(ValueError):
            await document_processor.process_image(b"invalid image content")


class TestEmbeddingService:
    """Test embedding generation."""
    
    @pytest.mark.asyncio
    async def test_embed_single_text(self):
        """Test embedding a single text."""
        service = EmbeddingService(model_name="all-MiniLM-L6-v2")
        
        embedding = await service.embed_text("This is a test sentence.")
        
        assert isinstance(embedding, list)
        assert len(embedding) == service.embedding_dimension
        assert all(isinstance(x, float) for x in embedding)
    
    @pytest.mark.asyncio
    async def test_embed_multiple_texts(self):
        """Test embedding multiple texts."""
        service = EmbeddingService(model_name="all-MiniLM-L6-v2")
        
        texts = [
            "First test sentence.",
            "Second test sentence.",
            "Third test sentence."
        ]
        
        embeddings = await service.embed_texts(texts)
        
        assert len(embeddings) == len(texts)
        assert all(len(emb) == service.embedding_dimension for emb in embeddings)
    
    @pytest.mark.asyncio
    async def test_embed_empty_text_raises_error(self):
        """Test embedding empty text raises error."""
        service = EmbeddingService(model_name="all-MiniLM-L6-v2")
        
        with pytest.raises(ValueError):
            await service.embed_text("")


class TestVectorStore:
    """Test vector store operations."""
    
    def test_add_and_search_vectors(self):
        """Test adding vectors and searching."""
        store = VectorStore(dimension=384)
        
        # Create test vectors
        vectors = [
            [0.1] * 384,
            [0.2] * 384,
            [0.3] * 384
        ]
        
        metadata = [
            {"text": "First chunk", "page": 1},
            {"text": "Second chunk", "page": 2},
            {"text": "Third chunk", "page": 3}
        ]
        
        # Add vectors
        store.add_vectors(vectors, metadata)
        
        assert store.size() == 3
        
        # Search
        query_vector = [0.15] * 384
        results = store.search(query_vector, top_k=2)
        
        assert len(results) == 2
        assert all(isinstance(r[0], dict) for r in results)
        assert all(isinstance(r[1], float) for r in results)
    
    def test_clear_vectors(self):
        """Test clearing all vectors."""
        store = VectorStore(dimension=384)
        
        vectors = [[0.1] * 384]
        metadata = [{"text": "Test", "page": 1}]
        
        store.add_vectors(vectors, metadata)
        assert store.size() == 1
        
        store.clear()
        assert store.size() == 0
    
    def test_search_empty_store(self):
        """Test searching empty store returns empty results."""
        store = VectorStore(dimension=384)
        
        query_vector = [0.1] * 384
        results = store.search(query_vector, top_k=5)
        
        assert len(results) == 0


class TestSessionManager:
    """Test session management."""
    
    @pytest.mark.asyncio
    async def test_create_and_get_session(self, session_manager):
        """Test creating and retrieving a session."""
        # Create test data
        store = VectorStore(dimension=384)
        chunks = [DocumentChunk("Test text", 1, 0)]
        
        # Create session
        session_id = session_manager.create_session(store, chunks)
        
        assert session_id.startswith("s_")
        assert len(session_id) > 10
        
        # Get session
        context = session_manager.get_session(session_id)
        
        assert context is not None
        assert context.session_id == session_id
        assert len(context.chunks) == 1
    
    @pytest.mark.asyncio
    async def test_delete_session(self, session_manager):
        """Test deleting a session."""
        store = VectorStore(dimension=384)
        chunks = [DocumentChunk("Test text", 1, 0)]
        
        session_id = session_manager.create_session(store, chunks)
        
        # Delete session
        deleted = await session_manager.delete_session(session_id)
        
        assert deleted is True
        
        # Verify session is gone
        context = session_manager.get_session(session_id)
        assert context is None
    
    @pytest.mark.asyncio
    async def test_session_expiry(self):
        """Test session expires after TTL."""
        manager = SessionManager(default_ttl_minutes=0.01)  # 0.6 seconds
        await manager.start()
        
        try:
            store = VectorStore(dimension=384)
            chunks = [DocumentChunk("Test text", 1, 0)]
            
            session_id = manager.create_session(store, chunks)
            
            # Session should exist initially
            context = manager.get_session(session_id)
            assert context is not None
            
            # Wait for expiry
            await asyncio.sleep(1)
            
            # Session should be expired
            context = manager.get_session(session_id)
            assert context is None
            
        finally:
            await manager.stop()
    
    @pytest.mark.asyncio
    async def test_get_session_info(self, session_manager):
        """Test getting session information."""
        store = VectorStore(dimension=384)
        chunks = [DocumentChunk("Test text", 1, 0)]
        
        session_id = session_manager.create_session(
            store,
            chunks,
            metadata={"test": "value"}
        )
        
        info = session_manager.get_session_info(session_id)
        
        assert info is not None
        assert info["session_id"] == session_id
        assert info["chunk_count"] == 1
        assert info["metadata"]["test"] == "value"


class TestDocumentAPI:
    """Test document API endpoints."""
    
    def test_upload_pdf_endpoint(self, client, sample_pdf_bytes):
        """Test PDF upload endpoint."""
        # Mock the RAG service to avoid actual processing
        with patch('backend.services.rag_service.RAGService.process_pdf') as mock_process:
            mock_process.return_value = "s_test123"
            
            response = client.post(
                "/api/v1/documents",
                files={"file": ("test.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            assert "session_id" in data["data"]
            assert "expires_in_minutes" in data["data"]
            assert "privacy" in data
    
    def test_upload_image_endpoint(self, client, sample_image_bytes):
        """Test image upload endpoint."""
        with patch('backend.services.rag_service.RAGService.process_image') as mock_process:
            mock_process.return_value = "s_test456"
            
            response = client.post(
                "/api/v1/documents",
                files={"file": ("test.png", io.BytesIO(sample_image_bytes), "image/png")}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            assert "session_id" in data["data"]
    
    def test_upload_invalid_file_type(self, client):
        """Test uploading invalid file type."""
        response = client.post(
            "/api/v1/documents",
            files={"file": ("test.txt", io.BytesIO(b"text content"), "text/plain")}
        )
        
        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False
    
    def test_upload_file_too_large(self, client):
        """Test uploading file that's too large."""
        # Create a large file (> 30 MB)
        large_content = b"x" * (31 * 1024 * 1024)
        
        response = client.post(
            "/api/v1/documents",
            files={"file": ("large.pdf", io.BytesIO(large_content), "application/pdf")}
        )
        
        assert response.status_code == 413
        data = response.json()
        assert data["success"] is False
    
    def test_query_session_endpoint(self, client):
        """Test querying a document session."""
        with patch('backend.services.rag_service.RAGService.query_session') as mock_query:
            mock_query.return_value = {
                "reply": "Test answer",
                "source_chunks": [{"page": 1, "excerpt": "Test excerpt", "type": "text"}],
                "metadata": {"chunks_retrieved": 1, "model": "gemini-2.0-flash"}
            }
            
            response = client.post(
                "/api/v1/documents/sessions/s_test123/query",
                json={"message": "What is this about?"}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            assert "reply" in data["data"]
            assert "source_chunks" in data["data"]
            assert "model_info" in data["data"]
    
    def test_query_nonexistent_session(self, client):
        """Test querying a session that doesn't exist."""
        with patch('backend.services.rag_service.RAGService.query_session') as mock_query:
            mock_query.side_effect = ValueError("Session not found")
            
            response = client.post(
                "/api/v1/documents/sessions/s_nonexistent/query",
                json={"message": "Test query"}
            )
            
            assert response.status_code == 404
    
    def test_delete_session_endpoint(self, client):
        """Test deleting a session."""
        with patch('backend.services.session_manager.SessionManager.delete_session') as mock_delete:
            mock_delete.return_value = True
            
            response = client.delete("/api/v1/documents/sessions/s_test123")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            assert data["data"]["deleted"] is True
    
    def test_delete_nonexistent_session(self, client):
        """Test deleting a session that doesn't exist."""
        with patch('backend.services.session_manager.SessionManager.delete_session') as mock_delete:
            mock_delete.return_value = False
            
            response = client.delete("/api/v1/documents/sessions/s_nonexistent")
            
            assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
