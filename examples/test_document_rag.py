"""
Example script to test the ephemeral multi-modal RAG API.
Demonstrates uploading a document, querying it, and cleaning up.
"""

import requests
import json
import time
from pathlib import Path


# Configuration
API_BASE_URL = "http://localhost:8000"
DOCUMENTS_ENDPOINT = f"{API_BASE_URL}/api/v1/documents"


def create_test_pdf():
    """Create a simple test PDF for demonstration."""
    try:
        import fitz  # PyMuPDF
        
        pdf = fitz.open()
        
        # Page 1
        page1 = pdf.new_page()
        page1.insert_text(
            (50, 50),
            "Machine Learning Research Paper",
            fontsize=16
        )
        page1.insert_text(
            (50, 100),
            "Abstract: This paper presents a novel approach to neural network optimization.",
            fontsize=12
        )
        page1.insert_text(
            (50, 130),
            "We achieved 95% accuracy on the benchmark dataset using our new method.",
            fontsize=12
        )
        
        # Page 2
        page2 = pdf.new_page()
        page2.insert_text(
            (50, 50),
            "Methodology",
            fontsize=14
        )
        page2.insert_text(
            (50, 80),
            "We used a convolutional neural network with 5 layers.",
            fontsize=12
        )
        page2.insert_text(
            (50, 110),
            "Training was performed on 10,000 images over 100 epochs.",
            fontsize=12
        )
        
        # Page 3
        page3 = pdf.new_page()
        page3.insert_text(
            (50, 50),
            "Results",
            fontsize=14
        )
        page3.insert_text(
            (50, 80),
            "Our model achieved 95% accuracy on the test set.",
            fontsize=12
        )
        page3.insert_text(
            (50, 110),
            "Training time was reduced by 40% compared to baseline methods.",
            fontsize=12
        )
        
        # Save to bytes
        pdf_bytes = pdf.tobytes()
        pdf.close()
        
        return pdf_bytes
    
    except ImportError:
        print("PyMuPDF not installed. Please install: pip install PyMuPDF")
        return None


def upload_document(file_path=None, file_bytes=None):
    """Upload a document to the API.
    
    Args:
        file_path: Path to file to upload (optional)
        file_bytes: File bytes to upload (optional)
    
    Returns:
        Session ID if successful, None otherwise
    """
    print("\n" + "="*60)
    print("STEP 1: Uploading Document")
    print("="*60)
    
    try:
        if file_path:
            with open(file_path, 'rb') as f:
                files = {'file': (Path(file_path).name, f, 'application/pdf')}
                response = requests.post(DOCUMENTS_ENDPOINT, files=files)
        elif file_bytes:
            files = {'file': ('test_document.pdf', file_bytes, 'application/pdf')}
            response = requests.post(DOCUMENTS_ENDPOINT, files=files)
        else:
            print("Error: No file provided")
            return None
        
        if response.status_code == 200:
            data = response.json()
            session_id = data['data']['session_id']
            expires_in = data['data']['expires_in_minutes']
            processing_time = data['data']['processing_time_ms']
            
            print(f"✓ Document uploaded successfully!")
            print(f"  Session ID: {session_id}")
            print(f"  Expires in: {expires_in} minutes")
            print(f"  Processing time: {processing_time}ms")
            print(f"\n  Privacy: {data.get('privacy', 'N/A')}")
            
            return session_id
        else:
            print(f"✗ Upload failed: {response.status_code}")
            print(f"  Error: {response.json()}")
            return None
    
    except Exception as e:
        print(f"✗ Upload error: {e}")
        return None


def query_document(session_id, question):
    """Query a document session.
    
    Args:
        session_id: Session ID from upload
        question: Question to ask
    
    Returns:
        Response data if successful, None otherwise
    """
    print(f"\nQuestion: {question}")
    print("-" * 60)
    
    try:
        url = f"{DOCUMENTS_ENDPOINT}/sessions/{session_id}/query"
        payload = {"message": question}
        
        start_time = time.time()
        response = requests.post(url, json=payload)
        elapsed_time = int((time.time() - start_time) * 1000)
        
        if response.status_code == 200:
            data = response.json()
            reply = data['data']['reply']
            source_chunks = data['data']['source_chunks']
            model_info = data['data']['model_info']
            
            print(f"Answer: {reply}\n")
            
            if source_chunks:
                print("Sources:")
                for i, chunk in enumerate(source_chunks, 1):
                    print(f"  {i}. Page {chunk['page']} ({chunk['type']})")
                    print(f"     \"{chunk['excerpt'][:100]}...\"")
            
            print(f"\nMetadata:")
            print(f"  Model: {model_info['model']}")
            print(f"  Latency: {model_info['latency_ms']}ms")
            print(f"  Chunks retrieved: {model_info['chunks_retrieved']}")
            print(f"  Total time: {elapsed_time}ms")
            
            return data
        else:
            print(f"✗ Query failed: {response.status_code}")
            print(f"  Error: {response.json()}")
            return None
    
    except Exception as e:
        print(f"✗ Query error: {e}")
        return None


def delete_session(session_id):
    """Delete a document session.
    
    Args:
        session_id: Session ID to delete
    
    Returns:
        True if successful, False otherwise
    """
    print("\n" + "="*60)
    print("STEP 3: Deleting Session")
    print("="*60)
    
    try:
        url = f"{DOCUMENTS_ENDPOINT}/sessions/{session_id}"
        response = requests.delete(url)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Session deleted successfully!")
            print(f"  {data['message']}")
            return True
        else:
            print(f"✗ Delete failed: {response.status_code}")
            print(f"  Error: {response.json()}")
            return False
    
    except Exception as e:
        print(f"✗ Delete error: {e}")
        return False


def main():
    """Main test flow."""
    print("\n" + "="*60)
    print("Ephemeral Multi-Modal RAG API Test")
    print("="*60)
    
    # Create test PDF
    print("\nCreating test PDF...")
    pdf_bytes = create_test_pdf()
    
    if pdf_bytes is None:
        print("Failed to create test PDF. Exiting.")
        return
    
    print(f"✓ Test PDF created ({len(pdf_bytes)} bytes)")
    
    # Upload document
    session_id = upload_document(file_bytes=pdf_bytes)
    
    if session_id is None:
        print("\nTest failed: Could not upload document")
        return
    
    # Query document
    print("\n" + "="*60)
    print("STEP 2: Querying Document")
    print("="*60)
    
    questions = [
        "What is the main topic of this document?",
        "What accuracy did the model achieve?",
        "What methodology was used in the study?",
        "How long did the training take?"
    ]
    
    for question in questions:
        result = query_document(session_id, question)
        if result is None:
            print(f"\nTest failed: Could not query document")
            break
        time.sleep(1)  # Brief pause between queries
    
    # Delete session
    delete_session(session_id)
    
    print("\n" + "="*60)
    print("Test Complete!")
    print("="*60)


if __name__ == "__main__":
    main()
