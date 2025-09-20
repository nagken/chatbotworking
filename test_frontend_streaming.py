#!/usr/bin/env python3
"""
Test frontend streaming functionality
"""
import requests
import json

def test_chat_streaming():
    """Test the streaming chat endpoint"""
    print("🧪 Testing frontend streaming...")
    
    # Test chat endpoint
    url = "http://127.0.0.1:5000/api/chat/stream"
    
    # Login first to get session
    login_url = "http://127.0.0.1:5000/api/auth/login"
    login_data = {
        "email": "admin@pss-knowledge-assist.com",
        "password": "admin123"
    }
    
    session = requests.Session()
    login_response = session.post(login_url, json=login_data)
    print(f"🔐 Login status: {login_response.status_code}")
    
    if login_response.status_code == 200:
        login_result = login_response.json()
        print(f"✅ Login successful: {login_result.get('success')}")
        
        # Test streaming chat
        chat_data = {
            "message": "What is contraceptive coverage?",
            "conversation_id": None
        }
        
        print(f"🌊 Sending streaming request...")
        response = session.post(url, json=chat_data, stream=True)
        print(f"📡 Response status: {response.status_code}")
        print(f"📋 Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("📦 Streaming response chunks:")
            chunk_count = 0
            for line in response.iter_lines(decode_unicode=True):
                if line.startswith('data: '):
                    chunk_count += 1
                    try:
                        data = json.loads(line[6:])  # Remove 'data: ' prefix
                        print(f"  Chunk {chunk_count}: {data.get('type', 'unknown')} - {json.dumps(data, indent=2)[:200]}...")
                        
                        # Check for insights messages
                        if data.get('type') == 'chunk' and data.get('data', {}).get('type') == 'system_message':
                            chunk_data = data.get('data', {})
                            if chunk_data.get('message_type') == 'insights':
                                print(f"🧠 FOUND INSIGHTS MESSAGE!")
                                print(f"   Data structure: {json.dumps(chunk_data, indent=2)}")
                                
                    except json.JSONDecodeError as e:
                        print(f"  ❌ Failed to parse chunk: {line[:100]}...")
                        
            print(f"📊 Total chunks received: {chunk_count}")
        else:
            print(f"❌ Chat request failed: {response.text}")
    else:
        print(f"❌ Login failed: {login_response.text}")

if __name__ == "__main__":
    test_chat_streaming()