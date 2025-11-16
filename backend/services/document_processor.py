"""
Document processing service for extracting text and images from PDFs and images.
All operations are performed in-memory without disk persistence.
"""

import io
import logging
from typing import List, Dict, Any, Tuple
from PIL import Image
import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


class DocumentChunk:
    """Represents a chunk of text extracted from a document."""
    
    def __init__(
        self,
        text: str,
        page: int,
        chunk_id: int,
        metadata: Dict[str, Any] = None
    ):
        self.text = text
        self.page = page
        self.chunk_id = chunk_id
        self.metadata = metadata or {}


class DocumentProcessor:
    """Service for processing documents in memory without disk persistence."""
    
    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 100):
        """Initialize document processor.
        
        Args:
            chunk_size: Target size for text chunks in characters
            chunk_overlap: Overlap between chunks in characters
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        logger.info(
            f"DocumentProcessor initialized (chunk_size={chunk_size}, "
            f"overlap={chunk_overlap})"
        )
    
    async def process_pdf(
        self,
        file_bytes: bytes
    ) -> Tuple[List[DocumentChunk], List[Tuple[bytes, int]]]:
        """Process PDF file in memory and extract text and images.
        
        Args:
            file_bytes: PDF file content as bytes
        
        Returns:
            Tuple of (text_chunks, images) where images is list of (image_bytes, page_num)
        
        Raises:
            ValueError: If PDF is invalid or cannot be processed
        """
        try:
            # Validate PDF bytes
            if not file_bytes:
                raise ValueError("PDF file is empty. Please ensure you're uploading a valid PDF file.")
            
            # Check for PDF header
            if not file_bytes.startswith(b'%PDF'):
                raise ValueError("File does not appear to be a valid PDF. The file header is missing or corrupted.")
            
            # Open PDF from memory
            pdf_document = fitz.open(stream=file_bytes, filetype="pdf")
            
            all_text = []
            images = []
            
            # Extract text and images from each page
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                
                # Extract text
                text = page.get_text()
                if text.strip():
                    all_text.append({
                        "text": text,
                        "page": page_num + 1
                    })
                
                # Extract images
                image_list = page.get_images()
                for img_index, img in enumerate(image_list):
                    try:
                        xref = img[0]
                        base_image = pdf_document.extract_image(xref)
                        image_bytes = base_image["image"]
                        images.append((image_bytes, page_num + 1))
                    except Exception as e:
                        logger.warning(
                            f"Failed to extract image {img_index} from page {page_num + 1}: {e}"
                        )
            
            pdf_document.close()
            
            # Create chunks from extracted text
            chunks = self._create_chunks(all_text)
            
            logger.info(
                f"Processed PDF: {len(chunks)} text chunks, {len(images)} images"
            )
            
            return chunks, images
            
        except ValueError:
            # Re-raise validation errors as-is
            raise
            
        except Exception as e:
            error_msg = str(e).lower()
            logger.error(f"Error processing PDF: {e}", exc_info=True)
            
            # Provide more helpful error messages
            if "no objects found" in error_msg or "failed to open stream" in error_msg:
                raise ValueError(
                    "The PDF file appears to be corrupted or invalid. "
                    "Please ensure you're uploading a valid, non-corrupted PDF file. "
                    "Try opening the file in a PDF reader to verify it's valid."
                )
            elif "password" in error_msg or "encrypted" in error_msg:
                raise ValueError("The PDF file is password-protected. Please upload an unencrypted PDF.")
            else:
                raise ValueError(f"Failed to process PDF: {str(e)}")
    
    async def process_image(
        self,
        file_bytes: bytes
    ) -> Tuple[bytes, Dict[str, Any]]:
        """Process image file in memory and validate.
        
        Args:
            file_bytes: Image file content as bytes
        
        Returns:
            Tuple of (image_bytes, metadata)
        
        Raises:
            ValueError: If image is invalid or cannot be processed
        """
        try:
            # Open and validate image
            image = Image.open(io.BytesIO(file_bytes))
            
            # Get image metadata
            metadata = {
                "format": image.format,
                "mode": image.mode,
                "size": image.size,
                "width": image.width,
                "height": image.height
            }
            
            # Convert to RGB if needed (for consistency)
            if image.mode not in ("RGB", "L"):
                image = image.convert("RGB")
            
            # Convert back to bytes
            output = io.BytesIO()
            image.save(output, format="PNG")
            processed_bytes = output.getvalue()
            
            logger.info(
                f"Processed image: {metadata['format']}, "
                f"{metadata['width']}x{metadata['height']}"
            )
            
            return processed_bytes, metadata
            
        except Exception as e:
            logger.error(f"Error processing image: {e}", exc_info=True)
            raise ValueError(f"Failed to process image: {str(e)}")
    
    def _create_chunks(self, text_pages: List[Dict[str, Any]]) -> List[DocumentChunk]:
        """Create overlapping text chunks from extracted text.
        
        Args:
            text_pages: List of dicts with 'text' and 'page' keys
        
        Returns:
            List of DocumentChunk objects
        """
        chunks = []
        chunk_id = 0
        
        for page_data in text_pages:
            text = page_data["text"]
            page_num = page_data["page"]
            
            # Split text into sentences (simple approach)
            sentences = self._split_into_sentences(text)
            
            current_chunk = []
            current_length = 0
            
            for sentence in sentences:
                sentence_length = len(sentence)
                
                # If adding this sentence exceeds chunk size, save current chunk
                if current_length + sentence_length > self.chunk_size and current_chunk:
                    chunk_text = " ".join(current_chunk)
                    chunks.append(
                        DocumentChunk(
                            text=chunk_text,
                            page=page_num,
                            chunk_id=chunk_id,
                            metadata={"char_count": len(chunk_text)}
                        )
                    )
                    chunk_id += 1
                    
                    # Keep overlap
                    overlap_text = chunk_text[-self.chunk_overlap:]
                    current_chunk = [overlap_text] if overlap_text else []
                    current_length = len(overlap_text)
                
                current_chunk.append(sentence)
                current_length += sentence_length
            
            # Add remaining text as final chunk for this page
            if current_chunk:
                chunk_text = " ".join(current_chunk)
                chunks.append(
                    DocumentChunk(
                        text=chunk_text,
                        page=page_num,
                        chunk_id=chunk_id,
                        metadata={"char_count": len(chunk_text)}
                    )
                )
                chunk_id += 1
        
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences (simple approach).
        
        Args:
            text: Input text
        
        Returns:
            List of sentences
        """
        # Simple sentence splitting (can be improved with nltk)
        import re
        
        # Split on sentence boundaries
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        # Filter out empty sentences
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences
