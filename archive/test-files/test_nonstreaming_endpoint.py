#!/usr/bin/env python3
"""
Test script for the non-streaming chat endpoint
This will help debug why the endpoint returns undefined
"""

import requests
import json
import sys

def test_nonstreaming_chat():
    """Test the non-streaming chat endpoint"""
    
    # Try different ports - update this based on which port your server starts on
    possible_ports = [8080, 5000, 8000, 3000]
    base_url = None
    
    for port in possible_ports:
        try:
            test_url = f"http://localhost:{port}"
            health_response = requests.get(f"{test_url}/api/health", timeout=2)
            if health_response.status_code == 200:
                base_url = test_url
                print(f"✅ Found server running on port {port}")
                break
        except:
            continue
    
    if not base_url:
        print("❌ No server found on common ports. Make sure server is running.")
        return
    
    # Test health first
    try:
        health_response = requests.get(f"{base_url}/api/health", timeout=5)
        print(f"🏥 Health Status: {health_response.status_code}")
        if health_response.status_code == 200:
            print(f"✅ Server is running and healthy at {base_url}")
        else:
            print(f"❌ Server health check failed: {health_response.text}")
            return
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return
    
    # Test login first
    login_url = f"{base_url}/api/auth/login"
    login_data = {
        "email": "john.smith@cvshealth.com",
        "password": "password123"
    }
    
    print("\n🔐 Testing login...")
    try:
        login_response = requests.post(login_url, json=login_data, timeout=10)
        print(f"Login Status: {login_response.status_code}")
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.text}")
            return
        
        login_result = login_response.json()
        token = login_result.get("access_token")
        if not token:
            print(f"❌ No access token in login response: {login_result}")
            return
            
        print(f"✅ Login successful, token: {token[:20]}...")
        
    except Exception as e:
        print(f"❌ Login request failed: {e}")
        return
    
    # Test chat endpoint
    chat_url = f"{base_url}/api/chat"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    chat_data = {
        "message": "Tell me about contraceptive coverage",
        "superclient": "CVS Pharmacy"
    }
    
    print(f"\n💬 Testing chat endpoint with message: '{chat_data['message']}'")
    
    try:
        chat_response = requests.post(chat_url, json=chat_data, headers=headers, timeout=30)
        print(f"Chat Status: {chat_response.status_code}")
        print(f"Chat Headers: {dict(chat_response.headers)}")
        
        if chat_response.status_code == 200:
            try:
                chat_result = chat_response.json()
                print(f"✅ Chat successful!")
                print(f"Response type: {type(chat_result)}")
                print(f"Response keys: {list(chat_result.keys()) if isinstance(chat_result, dict) else 'Not a dict'}")
                
                if isinstance(chat_result, dict):
                    print(f"Success: {chat_result.get('success')}")
                    print(f"Message preview: {str(chat_result.get('message', ''))[:200]}...")
                    
                    # Check if we have document results in the message
                    message_content = str(chat_result.get('message', ''))
                    if 'Related Documents' in message_content:
                        print("📚 ✅ Document search results found in response!")
                        # Show a snippet of the document section
                        doc_start = message_content.find('Related Documents')
                        doc_snippet = message_content[doc_start:doc_start+300]
                        print(f"Document snippet: {doc_snippet}...")
                    else:
                        print("⚠️ No document search results found in response")
                        
                    # Show full response for debugging
                    print(f"\n📄 Full Response JSON:")
                    print(json.dumps(chat_result, indent=2)[:1000] + "..." if len(str(chat_result)) > 1000 else json.dumps(chat_result, indent=2))
                        
                else:
                    print(f"❌ Unexpected response type: {type(chat_result)}")
                    print(f"Raw response: {chat_result}")
                    
            except json.JSONDecodeError as e:
                print(f"❌ Failed to parse JSON response: {e}")
                print(f"Raw response content: {chat_response.text}")
                print(f"Response length: {len(chat_response.text)}")
        else:
            print(f"❌ Chat failed with status {chat_response.status_code}")
            print(f"Error response: {chat_response.text}")
            
    except Exception as e:
        print(f"❌ Chat request failed: {e}")

if __name__ == "__main__":
    print("🧪 CVS Pharmacy Non-Streaming Chat Endpoint Test")
    print("=" * 50)
    test_nonstreaming_chat()
    print("\n" + "=" * 50)
    print("Test completed. Check the results above.")
