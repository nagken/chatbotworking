#!/usr/bin/env python3
"""
Test script to check frontend display issues
"""

import requests
import json
import time

def test_chat_response():
    print("🧪 Testing chat response display...")
    
    # Login first
    login_response = requests.post('http://127.0.0.1:5000/api/auth/login', 
        json={'email': 'admin@pss-knowledge-assist.com', 'password': 'password123'})
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        return
    
    session_token = login_response.json()['session_token']
    print("✅ Login successful")
    
    # Test the chat endpoint
    headers = {'Authorization': f'Bearer {session_token}'}
    chat_data = {
        'message': 'What is contraceptive coverage?',
        'conversation_id': None
    }
    
    print("🌊 Starting streaming request...")
    response = requests.post('http://127.0.0.1:5000/api/chat/stream',
        json=chat_data, headers=headers, stream=True)
    
    print(f"📡 Response status: {response.status_code}")
    
    if response.status_code == 200:
        print("📥 Processing streaming response...")
        chunk_count = 0
        
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                print(f"Raw line: {line[:100]}...")
                
                if line.startswith('data: '):
                    data_str = line[6:]  # Remove 'data: ' prefix
                    try:
                        data = json.loads(data_str)
                        chunk_count += 1
                        
                        print(f"\n=== CHUNK {chunk_count} ===")
                        print(f"Message type: {data.get('message_type', 'unknown')}")
                        
                        if 'data' in data:
                            data_content = data['data']
                            print(f"Data keys: {list(data_content.keys())}")
                            
                            if 'ai_insights' in data_content:
                                insights = data_content['ai_insights']
                                print(f"AI Insights found (length: {len(insights)})")
                                print(f"Insights preview: {insights[:200]}...")
                                
                                # Check for document links
                                if '<a href=' in insights:
                                    print("✅ Document links found in insights")
                                else:
                                    print("⚠️ No document links found")
                            else:
                                print("❌ No ai_insights in data")
                        
                        print(f"Full data: {json.dumps(data, indent=2)[:500]}...")
                        
                    except json.JSONDecodeError as e:
                        print(f"❌ JSON decode error: {e}")
                        print(f"Raw data: {data_str[:200]}...")
                
                # Stop after first few chunks to avoid spam
                if chunk_count >= 2:
                    break
    else:
        print(f"❌ Request failed: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    test_chat_response()