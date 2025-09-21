#!/usr/bin/env python3
"""
Direct streaming test to mimic browser behavior and monitor message flow
"""
import requests
import json
import time

def test_streaming_chat():
    """Test the streaming chat to see the exact message flow"""
    print("🧪 Testing CVS Pharmacy Knowledge Assist streaming...")
    
    # Login first
    login_url = "http://127.0.0.1:5000/api/auth/login"
    login_data = {
        "email": "admin@pss-knowledge-assist.com", 
        "password": "admin123"
    }
    
    session = requests.Session()
    login_response = session.post(login_url, json=login_data)
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.text}")
        return
        
    print(f"✅ Login successful")
    
    # Now test streaming chat
    chat_url = "http://127.0.0.1:5000/api/chat/stream"
    chat_data = {
        "message": "What is contraceptive coverage?",
        "conversation_id": None
    }
    
    print(f"🌊 Sending streaming request: '{chat_data['message']}'")
    
    response = session.post(chat_url, json=chat_data, stream=True)
    print(f"📡 Response status: {response.status_code}")
    
    if response.status_code == 200:
        print("📦 Streaming response chunks:")
        chunk_count = 0
        insights_found = False
        
        for line in response.iter_lines(decode_unicode=True):
            if line and line.startswith('data: '):
                chunk_count += 1
                try:
                    data = json.loads(line[6:])  # Remove 'data: ' prefix
                    chunk_type = data.get('type', 'unknown')
                    print(f"  📋 Chunk {chunk_count}: type='{chunk_type}'")
                    
                    # Look for insights messages
                    if chunk_type == 'chunk':
                        chunk_data = data.get('data', {})
                        if chunk_data.get('type') == 'system_message':
                            message_type = chunk_data.get('message_type')
                            print(f"    🎯 System message: type='{message_type}'")
                            
                            if message_type == 'insights':
                                insights_found = True
                                insights_data = chunk_data.get('data', {})
                                ai_insights = insights_data.get('ai_insights', '')
                                print(f"    🧠 INSIGHTS FOUND!")
                                print(f"    📝 Content preview: {ai_insights[:150]}...")
                                print(f"    📊 Full data structure:")
                                print(json.dumps(chunk_data, indent=4))
                                
                except json.JSONDecodeError as e:
                    print(f"  ❌ JSON parse error: {line[:100]}...")
                    
        print(f"\n📊 Summary:")
        print(f"  - Total chunks: {chunk_count}")
        print(f"  - Insights found: {'✅ YES' if insights_found else '❌ NO'}")
        
    else:
        print(f"❌ Chat request failed: {response.text}")

if __name__ == "__main__":
    test_streaming_chat()