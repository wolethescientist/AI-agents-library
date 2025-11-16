"""
Quick test script to verify file upload integration.
Run this after starting the server with: uvicorn backend.main:app --reload
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_standard_chat():
    """Test 1: Standard chat (backward compatibility)"""
    print("\n" + "="*60)
    print("TEST 1: Standard Chat (Backward Compatible)")
    print("="*60)
    
    response = requests.post(
        f"{BASE_URL}/api/v1/agents/physics",
        json={"message": "What is Newton's second law?"}
    )
    
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Mode: {data['data'].get('mode', 'N/A')}")
    print(f"Message Type: {data['data'].get('message_type', 'N/A')}")
    print(f"Reply: {data['data']['reply'][:100]}...")
    print("✅ PASSED" if response.status_code == 200 else "❌ FAILED")


def test_file_upload():
    """Test 2: File upload (requires a test PDF)"""
    print("\n" + "="*60)
    print("TEST 2: File Upload")
    print("="*60)
    
    # Create a simple test PDF content
    test_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/Resources <<\n/Font <<\n/F1 <<\n/Type /Font\n/Subtype /Type1\n/BaseFont /Helvetica\n>>\n>>\n>>\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n100 700 Td\n(Test PDF) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\n0000000317 00000 n\ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n410\n%%EOF"
    
    files = {
        'file': ('test.pdf', test_content, 'application/pdf')
    }
    data = {
        'message': 'Help me understand this document'
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/agents/physics",
            files=files,
            data=data
        )
        
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Mode: {result['data'].get('mode', 'N/A')}")
        print(f"Message Type: {result['data'].get('message_type', 'N/A')}")
        print(f"Session ID: {result['data'].get('session_id', 'N/A')}")
        print(f"Reply: {result['data']['reply'][:100]}...")
        print("✅ PASSED" if response.status_code == 200 else "❌ FAILED")
        
        return result['data'].get('session_id')
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return None


def test_document_query(session_id):
    """Test 3: Document query with session"""
    print("\n" + "="*60)
    print("TEST 3: Document Query with Session")
    print("="*60)
    
    if not session_id:
        print("⚠️  SKIPPED: No session ID from previous test")
        return
    
    data = {
        'message': 'What is on page 1?',
        'session_id': session_id
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/agents/physics",
            data=data
        )
        
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Mode: {result['data'].get('mode', 'N/A')}")
        print(f"Message Type: {result['data'].get('message_type', 'N/A')}")
        print(f"Session ID: {result['data'].get('session_id', 'N/A')}")
        print(f"Reply: {result['data']['reply'][:100]}...")
        print("✅ PASSED" if response.status_code == 200 else "❌ FAILED")
    except Exception as e:
        print(f"❌ FAILED: {e}")


def test_general_query_with_session(session_id):
    """Test 4: General query with active session (fallback)"""
    print("\n" + "="*60)
    print("TEST 4: General Query with Active Session (Fallback)")
    print("="*60)
    
    if not session_id:
        print("⚠️  SKIPPED: No session ID from previous test")
        return
    
    data = {
        'message': 'What is the speed of light?',
        'session_id': session_id
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/agents/physics",
            data=data
        )
        
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Mode: {result['data'].get('mode', 'N/A')}")
        print(f"Message Type: {result['data'].get('message_type', 'N/A')}")
        print(f"Fallback Reason: {result['data']['metadata'].get('fallback_reason', 'N/A')}")
        print(f"Reply: {result['data']['reply'][:100]}...")
        print("✅ PASSED" if response.status_code == 200 and result['data'].get('mode') == 'general' else "❌ FAILED")
    except Exception as e:
        print(f"❌ FAILED: {e}")


def test_list_agents():
    """Test 5: List agents (verify no breaking changes)"""
    print("\n" + "="*60)
    print("TEST 5: List Agents (Backward Compatibility)")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/api/v1/agents/")
    
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Agents found: {len(data['data']['agents'])}")
    print("✅ PASSED" if response.status_code == 200 else "❌ FAILED")


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("FILE & IMAGE UPLOAD INTEGRATION TESTS")
    print("="*60)
    print("\nMake sure the server is running:")
    print("  uvicorn backend.main:app --reload")
    print("\nStarting tests in 3 seconds...")
    
    import time
    time.sleep(3)
    
    try:
        # Test 1: Standard chat
        test_standard_chat()
        
        # Test 2: File upload
        session_id = test_file_upload()
        
        # Test 3: Document query
        test_document_query(session_id)
        
        # Test 4: General query with session
        test_general_query_with_session(session_id)
        
        # Test 5: List agents
        test_list_agents()
        
        print("\n" + "="*60)
        print("ALL TESTS COMPLETED")
        print("="*60)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to server")
        print("Make sure the server is running:")
        print("  uvicorn backend.main:app --reload")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")


if __name__ == "__main__":
    main()
