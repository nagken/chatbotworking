#!/usr/bin/env python3
"""Test streaming chat response for document search integration."""

import requests
import json
import time

def test_streaming_chat():
    """Test the streaming chat endpoint with a mail order query."""
    url = "http://127.0.0.1:8080/api/chat/stream"
    
    # Test payload for mail order history query
    payload = {
        "message": "How do I access a member's mail order history?",
        "conversation_id": "test-123",
        "user_id": "test@cvs.com"
    }
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "text/plain"
    }
    
    print("🧪 Testing streaming chat with mail order query...")
    print(f"📤 Payload: {json.dumps(payload, indent=2)}")
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
        for chunk in response.iter_lines(decode_unicode=True):
            if chunk:
                print(f"🔥 Chunk: {chunk}")
                
                # Try to parse as JSON if it looks like JSON
                if chunk.startswith('data: '):
                    data_part = chunk[6:]  # Remove 'data: ' prefix
                    try:
                        parsed = json.loads(data_part)
                        print(f"📊 Parsed JSON: {json.dumps(parsed, indent=2)}")
                    except json.JSONDecodeError:
                        print(f"📝 Raw data: {data_part}")
                
                print("-" * 20)
        
        print("=" * 60)
        print("✅ Streaming test completed")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    
    return True

def test_non_streaming_chat():
    """Test the non-streaming chat endpoint for comparison."""
    url = "http://127.0.0.1:8080/api/chat"
    
    payload = {
        "message": "How do I access a member's mail order history?",
        "conversation_id": "test-456",
        "user_id": "test@cvs.com"
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    print("\n🧪 Testing non-streaming chat for comparison...")
    print(f"📤 Payload: {json.dumps(payload, indent=2)}")
    print("=" * 60)
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        
        print(f"📈 Status Code: {response.status_code}")
        print(f"📋 Response Headers: {dict(response.headers)}")
        print("=" * 60)
        
        if response.status_code == 200:
            result = response.json()
            print(f"📥 Response: {json.dumps(result, indent=2)}")
        else:
            print(f"❌ Error Response: {response.text}")
        
        print("=" * 60)
        print("✅ Non-streaming test completed")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Testing CVS Pharmacy chatbot streaming responses...")
    print("🎯 Focus: Document search integration for mail order queries")
    print("=" * 80)
    
    # Test streaming endpoint
    success1 = test_streaming_chat()
    
    # Test non-streaming endpoint for comparison
    success2 = test_non_streaming_chat()
    
    print("\n" + "=" * 80)
    if success1 and success2:
        print("✅ All tests completed successfully!")
    else:
        print("❌ Some tests failed - check the output above")
