#!/usr/bin/env python3
"""
Complete streaming test with proper authentication
"""

import requests
import json
import time

def test_with_authentication():
    """Test streaming with proper authentication"""
    
    print("🧪 Testing CVS Pharmacy Knowledge Assist Streaming (With Auth)")
    print("=" * 60)
    
    base_url = "http://localhost:5000"
    
    # Step 1: Login to get a valid token
    print("🔐 Step 1: Logging in...")
    login_data = {
        "username": "admin@cvs-pharmacy-knowledge-assist.com", 
        "password": "admin123"
    }
    
    try:
        login_response = requests.post(f"{base_url}/api/auth/login", json=login_data)
        print(f"Login Status: {login_response.status_code}")
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.text}")
            
            # Try fallback credentials
            print("\n🔄 Trying fallback credentials...")
            fallback_data = {"username": "dev@cvs.com", "password": "dev123"}
            login_response = requests.post(f"{base_url}/api/auth/login", json=fallback_data)
            print(f"Fallback Login Status: {login_response.status_code}")
            
            if login_response.status_code != 200:
                print(f"❌ Fallback login also failed: {login_response.text}")
                return
        
        login_result = login_response.json()
        token = login_result.get("session_token") or login_result.get("access_token")
        
        if not token:
            print(f"❌ No token in login response: {login_result}")
            return
            
        print(f"✅ Login successful! Token: {token[:20]}...")
        
    except Exception as e:
        print(f"❌ Login error: {e}")
        return
    
    # Step 2: Test streaming with valid token
    print(f"\n🌊 Step 2: Testing streaming...")
    
    stream_url = f"{base_url}/api/chat/stream"
    test_message = "How do I process a prescription refill for a member?"
    
    payload = {
        "message": test_message,
        "conversation_id": None
    }
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
        "Authorization": f"Bearer {token}"
    }
    
    try:
        print(f"📡 Sending streaming request...")
        print(f"Message: {test_message}")
        
        response = requests.post(stream_url, json=payload, headers=headers, stream=True, timeout=30)
        
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Streaming failed: {response.text}")
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
                                break
                                
                except json.JSONDecodeError as e:
                    print(f"     ❌ JSON Parse Error: {e}")
                    print(f"     Raw line: {line}")
        
        # Show results
        print(f"\n📝 STREAMING TEST RESULTS:")
        print(f"{'='*60}")
        print(f"Total Messages: {message_count}")
        print(f"Response Length: {len(full_response)} characters")
        
        if full_response:
            print(f"\n💬 Complete Response:")
            print(f"{'-'*40}")
            print(full_response)
            print(f"{'-'*40}")
            
            # Check for document integration
            if "Related Documents:" in full_response:
                print("\n🔍 ✅ DOCUMENT SEARCH INTEGRATION DETECTED!")
                print("Document search is working correctly!")
            else:
                print("\n⚠️ No document search results found in response")
                
            print("\n🎉 STREAMING IS WORKING CORRECTLY!")
        else:
            print("\n❌ No content received in streaming response")
            
    except Exception as e:
        print(f"❌ Streaming test failed: {e}")

def test_without_auth():
    """Test streaming without auth (should fail but show us error)"""
    print("\n🔓 Testing streaming without authentication...")
    
    url = "http://localhost:5000/api/chat/stream"
    payload = {"message": "test", "conversation_id": None}
    headers = {"Content-Type": "application/json", "Accept": "text/event-stream"}
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=5)
        print(f"No-auth Status: {response.status_code}")
        print(f"No-auth Response: {response.text[:200]}...")
    except Exception as e:
        print(f"No-auth Error: {e}")

if __name__ == "__main__":
    test_with_authentication()
    test_without_auth()
