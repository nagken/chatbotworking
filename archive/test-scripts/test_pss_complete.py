#!/usr/bin/env python3
"""
Complete PSS Knowledge Assist Test
Tests login, chat streaming, and feedback functionality
"""

import requests
import json
import time


def test_pss_complete():
    """Test the complete PSS Knowledge Assist flow"""
    base_url = "http://127.0.0.1:8080"
    
    print("🧪 PSS Knowledge Assist Complete Test")
    print("=" * 50)
    
    # Test 1: Login
    print("\n1. Testing login...")
    login_response = requests.post(f"{base_url}/api/auth/login", json={
        "email": "admin@pss-knowledge-assist.com",
        "password": "admin123"
    })
    
    print(f"   Login Status: {login_response.status_code}")
    if login_response.status_code == 200:
        login_data = login_response.json()
        session_token = login_data.get('session_token')
        print(f"   ✅ Login successful - Token: {session_token[:20]}...")
    else:
        print(f"   ❌ Login failed: {login_response.text}")
        return
    
    # Test 2: Get conversations (should return mock data)
    print("\n2. Testing conversations...")
    headers = {"Authorization": f"Bearer {session_token}"}
    conversations_response = requests.get(f"{base_url}/api/conversations", headers=headers)
    
    print(f"   Conversations Status: {conversations_response.status_code}")
    if conversations_response.status_code == 200:
        conversations = conversations_response.json()
        print(f"   ✅ Found {len(conversations)} conversations")
        for conv in conversations[:2]:  # Show first 2
            print(f"      - {conv['title']}")
    else:
        print(f"   ❌ Conversations failed: {conversations_response.text}")
    
    # Test 3: Test chat streaming (should return mock PSS response)
    print("\n3. Testing chat streaming...")
    
    chat_data = {
        "message": "What PSS benefits are available?",
        "superclient": "PSS"
    }
    
    try:
        # Use streaming endpoint
        stream_response = requests.post(
            f"{base_url}/api/chat/stream", 
            json=chat_data, 
            headers=headers,
            stream=True,
            timeout=30
        )
        
        print(f"   Streaming Status: {stream_response.status_code}")
        if stream_response.status_code == 200:
            print("   ✅ Streaming response:")
            response_count = 0
            for line in stream_response.iter_lines():
                if line.startswith(b'data: '):
                    try:
                        data = json.loads(line[6:])  # Remove 'data: ' prefix
                        response_count += 1
                        print(f"      [{response_count}] {data.get('type', 'unknown')}: {data.get('content', data.get('message', 'No content'))[:100]}...")
                        
                        if data.get('type') == 'complete':
                            print(f"      ✅ Streaming completed successfully")
                            break
                            
                        if response_count > 10:  # Prevent infinite loop
                            print("      ⚠️ Too many responses, stopping...")
                            break
                    except json.JSONDecodeError:
                        continue
        else:
            print(f"   ❌ Streaming failed: {stream_response.text}")
    
    except Exception as e:
        print(f"   ❌ Streaming error: {e}")
    
    # Test 4: Test feedback submission
    print("\n4. Testing feedback submission...")
    
    feedback_data = {
        "message_id": "test-message-123",
        "rating": "positive",
        "comment": "Great PSS information!"
    }
    
    feedback_response = requests.post(
        f"{base_url}/api/feedback/submit", 
        json=feedback_data, 
        headers=headers
    )
    
    print(f"   Feedback Status: {feedback_response.status_code}")
    if feedback_response.status_code == 200:
        feedback_result = feedback_response.json()
        print(f"   ✅ Feedback submitted: {feedback_result.get('message', 'Success')}")
    else:
        print(f"   ❌ Feedback failed: {feedback_response.text}")
    
    # Test 5: Test quick test endpoint
    print("\n5. Testing system health...")
    
    health_response = requests.get(f"{base_url}/quick-test")
    print(f"   Health Status: {health_response.status_code}")
    if health_response.status_code == 200:
        health_data = health_response.json()
        print(f"   ✅ System healthy: {health_data.get('message', 'OK')}")
        print(f"      Auth: {health_data.get('auth_status', 'Unknown')}")
        print(f"      DB: {health_data.get('database_status', 'Unknown')}")
        print(f"      LLM: {health_data.get('llm_status', 'Unknown')}")
    else:
        print(f"   ❌ Health check failed: {health_response.text}")
    
    print("\n" + "=" * 50)
    print("🎉 PSS Knowledge Assist test completed!")
    print("💡 Check the browser at http://127.0.0.1:8080 for full UI test")


if __name__ == "__main__":
    test_pss_complete()
