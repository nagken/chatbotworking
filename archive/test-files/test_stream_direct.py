#!/usr/bin/env python3
"""
Direct test of the streaming chat endpoint
"""

import requests
import json
import uuid

def test_stream_endpoint():
    """Test the chat stream endpoint directly"""
    url = "http://127.0.0.1:5000/api/chat/stream"
    
    # Generate a proper UUID for conversation_id
    conversation_id = str(uuid.uuid4())
    
    payload = {
        "message": "What is contraceptive coverage?",
        "conversation_id": conversation_id
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    print(f"🧪 Testing stream endpoint with conversation_id: {conversation_id}")
    print(f"📍 URL: {url}")
    print(f"📦 Payload: {json.dumps(payload, indent=2)}")
    print("=" * 60)
    
    try:
        response = requests.post(url, json=payload, headers=headers, stream=True)
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📊 Response Headers: {dict(response.headers)}")
        print("=" * 60)
        
        if response.status_code == 200:
            print("🌊 Streaming response:")
            chunk_count = 0
            
            for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
                if chunk:
                    chunk_count += 1
                    print(f"--- Chunk {chunk_count} ---")
                    print(repr(chunk))
                    print(chunk)
                    print("-" * 30)
                    
            print(f"✅ Stream completed. Total chunks: {chunk_count}")
        else:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"Response body: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception occurred: {e}")

if __name__ == "__main__":
    test_stream_endpoint()