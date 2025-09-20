#!/usr/bin/env python3
"""Test streaming chat response with proper authentication."""

import requests
import json
import time

def login_and_get_token():
    """Login and get session token for authentication."""
    login_url = "http://127.0.0.1:8080/api/auth/login"
    
    # Use the demo user credentials from auth.py
    login_payload = {
        "email": "demo@cvs-pharmacy-knowledge-assist.com",
        "password": "demo1234"
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    print("🔐 Attempting login...")
    print(f"📤 Login payload: {json.dumps(login_payload, indent=2)}")
    
    try:
        response = requests.post(login_url, json=login_payload, headers=headers)
        
        print(f"📈 Login Status Code: {response.status_code}")
        print(f"📋 Login Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"📥 Login Response: {json.dumps(result, indent=2)}")
            
            if result.get("success") and "token" in result:
                token = result["token"]
                print(f"✅ Login successful! Token: {token[:20]}...")
                return token
            else:
                print(f"❌ Login failed: {result.get('message', 'Unknown error')}")
                return None
        else:
            print(f"❌ Login error: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Login exception: {e}")
        return None

def test_streaming_chat_with_auth():
    """Test the streaming chat endpoint with proper authentication."""
    
    # First, get authentication token
    token = login_and_get_token()
    if not token:
        print("❌ Could not obtain authentication token")
        return False
    
    print("\n" + "=" * 60)
    
    url = "http://127.0.0.1:8080/api/chat/stream"
    
    # Test payload for mail order history query
    payload = {
        "message": "How do I access a member's mail order history?",
        "conversation_id": "test-123",
        "user_id": "demo@cvs-pharmacy-knowledge-assist.com"
    }
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "text/plain",
        "Authorization": f"Bearer {token}"
    }
    
    print("🧪 Testing streaming chat with mail order query...")
    print(f"📤 Payload: {json.dumps(payload, indent=2)}")
    print(f"🔑 Using token: {token[:20]}...")
    print("=" * 60)
    
    try:
        # Make streaming request
        response = requests.post(url, json=payload, headers=headers, stream=True)
        
        print(f"📈 Status Code: {response.status_code}")
        print(f"📋 Response Headers: {dict(response.headers)}")
        print("=" * 60)
        print("📥 Streaming Response:")
        print("-" * 40)
        
        # Process streaming response
        chunk_count = 0
        document_found = False
        
        for chunk in response.iter_lines(decode_unicode=True):
            if chunk:
                chunk_count += 1
                print(f"🔥 Chunk {chunk_count}: {chunk}")
                
                # Check for document-related content
                if "Related Documents" in chunk or "mail order" in chunk.lower() or "document" in chunk.lower():
                    document_found = True
                    print("📄 🎯 DOCUMENT CONTENT DETECTED!")
                
                # Try to parse as JSON if it looks like JSON
                if chunk.startswith('data: '):
                    data_part = chunk[6:]  # Remove 'data: ' prefix
                    try:
                        parsed = json.loads(data_part)
                        print(f"📊 Parsed JSON: {json.dumps(parsed, indent=2)}")
                        
                        # Check for document information in the parsed JSON
                        if "related_documents" in str(parsed).lower() or "documents" in str(parsed).lower():
                            document_found = True
                            print("📄 🎯 DOCUMENT INFO IN JSON!")
                        
                    except json.JSONDecodeError:
                        print(f"📝 Raw data: {data_part}")
                
                print("-" * 20)
        
        print("=" * 60)
        print(f"📊 Total chunks received: {chunk_count}")
        print(f"📄 Document content detected: {'✅ YES' if document_found else '❌ NO'}")
        print("✅ Streaming test completed")
        
        return chunk_count > 0
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_non_streaming_chat_with_auth():
    """Test the non-streaming chat endpoint with authentication."""
    
    # First, get authentication token
    token = login_and_get_token()
    if not token:
        print("❌ Could not obtain authentication token")
        return False
    
    print("\n" + "=" * 60)
    
    url = "http://127.0.0.1:8080/api/chat"
    
    payload = {
        "message": "How do I access a member's mail order history?",
        "conversation_id": "test-456",
        "user_id": "demo@cvs-pharmacy-knowledge-assist.com"
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    print("🧪 Testing non-streaming chat for comparison...")
    print(f"📤 Payload: {json.dumps(payload, indent=2)}")
    print(f"🔑 Using token: {token[:20]}...")
    print("=" * 60)
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        
        print(f"📈 Status Code: {response.status_code}")
        print(f"📋 Response Headers: {dict(response.headers)}")
        print("=" * 60)
        
        if response.status_code == 200:
            result = response.json()
            print(f"📥 Response: {json.dumps(result, indent=2)}")
            
            # Check for document information
            response_text = str(result)
            if "related_documents" in response_text.lower() or "mail order" in response_text.lower():
                print("📄 🎯 DOCUMENT INFO DETECTED IN RESPONSE!")
            else:
                print("📄 ❌ No document info detected")
        else:
            print(f"❌ Error Response: {response.text}")
        
        print("=" * 60)
        print("✅ Non-streaming test completed")
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing CVS Pharmacy chatbot with proper authentication...")
    print("🎯 Focus: Document search integration for mail order queries")
    print("=" * 80)
    
    # Test streaming endpoint
    success1 = test_streaming_chat_with_auth()
    
    # Test non-streaming endpoint for comparison
    success2 = test_non_streaming_chat_with_auth()
    
    print("\n" + "=" * 80)
    if success1 and success2:
        print("✅ All tests completed successfully!")
        print("🎯 Check the output above for document content detection")
    else:
        print("❌ Some tests failed - check the output above")
