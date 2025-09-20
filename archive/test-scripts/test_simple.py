#!/usr/bin/env python3
"""
Simple test to verify feedback endpoint
"""

import requests
import json

def test_simple():
    base_url = "http://127.0.0.1:8080"
    
    print("🔍 Testing server connectivity...")
    
    # Test 1: Check if server is running
    try:
        response = requests.get(f"{base_url}/quick-test", timeout=5)
        print(f"✅ Server is running - Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Server not accessible: {e}")
        return
    
    # Test 2: Login
    try:
        login_response = requests.post(f"{base_url}/api/auth/login", 
                                     json={"email": "admin@pss-knowledge-assist.com", "password": "admin123"},
                                     timeout=10)
        if login_response.status_code == 200:
            token = login_response.json().get('session_token')
            print(f"✅ Login successful - Token available: {bool(token)}")
            
            # Test 3: Feedback submission
            message_id = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
            feedback_data = {"is_positive": False, "feedback_comment": "Test feedback"}
            headers = {"Authorization": f"Bearer {token}"}
            
            feedback_response = requests.post(
                f"{base_url}/api/feedback/messages/{message_id}/feedback",
                json=feedback_data,
                headers=headers,
                timeout=10
            )
            
            print(f"Feedback Status: {feedback_response.status_code}")
            print(f"Feedback Response: {feedback_response.text}")
            
        else:
            print(f"❌ Login failed: {login_response.status_code}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_simple()
