#!/usr/bin/env python3

import requests
import json

# Test the actual AI response to see what documents it's finding
url = "http://127.0.0.1:5000/api/chat/stream"

# Login first
login_data = {
    "email": "admin@pss-knowledge-assist.com",
    "password": "admin123"
}

session = requests.Session()
login_response = session.post("http://127.0.0.1:5000/api/auth/login", json=login_data)

if login_response.status_code == 200:
    print("✅ Login successful")
    
    # Send contraceptive question and capture the full response
    chat_data = {
        "message": "What documents mention contraceptive coverage? List the exact filenames.",
        "conversation_id": None
    }
    
    print("🔍 Asking for document list...")
    response = session.post(url, json=chat_data, stream=True, timeout=60)
    
    if response.status_code == 200:
        print("📡 Response status: 200")
        print("📦 Streaming response chunks:")
        
        for line in response.iter_lines():
            if line:
                try:
                    # Parse the SSE format
                    line_text = line.decode('utf-8')
                    if line_text.startswith('data: '):
                        data_text = line_text[6:]  # Remove 'data: ' prefix
                        if data_text.strip() and data_text != '[DONE]':
                            chunk = json.loads(data_text)
                            
                            if chunk.get('type') == 'system_message' and chunk.get('message_type') == 'insights':
                                print("🎯 INSIGHTS FOUND!")
                                insights_content = chunk.get('data', {}).get('ai_insights', '')
                                print("📄 Full AI Response:")
                                print("=" * 80)
                                print(insights_content)
                                print("=" * 80)
                                break
                                
                except json.JSONDecodeError:
                    continue
    else:
        print(f"❌ Request failed: {response.status_code}")
        print(response.text)
else:
    print(f"❌ Login failed: {login_response.status_code}")
    print(login_response.text)