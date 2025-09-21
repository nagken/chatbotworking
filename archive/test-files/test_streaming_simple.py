#!/usr/bin/env python3
"""
Simple streaming test script using requests library
"""

import requests
import json
import time

def test_streaming_endpoint():
    """Test the streaming chat endpoint directly"""
    
    print("🧪 Testing CVS Pharmacy Knowledge Assist Streaming")
    print("=" * 50)
    
    url = "http://localhost:5000/api/chat/stream"
    
    test_message = "How do I process a prescription refill for a member?"
    
    print(f"🔍 Testing: {test_message}")
    print("-" * 40)
    
    payload = {
        "message": test_message,
        "conversation_id": None
    }
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
        "Authorization": "Bearer test-token"
    }
    
    try:
        print("📡 Sending request...")
        print(f"URL: {url}")
        print(f"Headers: {headers}")
        print(f"Payload: {payload}")
        
        response = requests.post(url, json=payload, headers=headers, stream=True, timeout=10)
        
        print(f"📊 Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code != 200:
            print(f"❌ Error Response: {response.text}")
            return
        
        print("🌊 Reading streaming response...")
        message_count = 0
        full_response = ""
        
        for line in response.iter_lines(decode_unicode=True):
            if line and line.startswith('data: '):
                try:
                    data = json.loads(line[6:])  # Remove 'data: '
                    message_count += 1
                    
                    print(f"  📦 Message {message_count}: {data.get('type', 'unknown')}")
                    
                    if data.get('type') == 'system_message':
                        message_type = data.get('message_type', 'unknown')
                        print(f"     Message Type: {message_type}")
                        
                        if message_type == 'text_response':
                            content = data.get('data', {}).get('content', '')
                            is_final = data.get('data', {}).get('is_final', False)
                            
                            if content:
                                full_response = content
                                print(f"     Content Length: {len(content)} chars")
                                print(f"     Preview: {content[:100]}...")
                                
                            if is_final:
                                print(f"     ✅ Final message received!")
                                print(f"\n📝 Complete Response:")
                                print(f"{'='*60}")
                                print(full_response)
                                print(f"{'='*60}")
                                
                                # Check for document references
                                if "Related Documents:" in full_response:
                                    print("\n🔍 ✅ Document search integration detected!")
                                else:
                                    print("\n⚠️ No document search results found in response")
                                
                                break
                                
                except json.JSONDecodeError as e:
                    print(f"     ❌ JSON Parse Error: {e}")
                    print(f"     Raw line: {line}")
        
        print(f"\n✅ Test completed. Total messages: {message_count}")
        
        if message_count == 0:
            print("❌ No streaming messages received!")
        elif not full_response:
            print("❌ No content received in streaming messages!")
        else:
            print("🎉 Streaming is working correctly!")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_streaming_endpoint()
