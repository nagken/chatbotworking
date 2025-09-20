#!/usr/bin/env python3
"""
Test the updated authentication system
"""
import requests
import json

def test_login_and_conversations():
    """Test login and then conversations API"""
    base_url = "http://127.0.0.1:8080"
    
    print("=== Testing Updated Authentication ===")
    
    # Step 1: Login
    print("1. Testing login...")
    login_data = {
        "email": "admin@pss-knowledge-assist.com",
        "password": "admin123",
        "remember_me": False
    }
    
    try:
        # Create a session to maintain cookies
        session = requests.Session()
        
        response = session.post(f"{base_url}/api/auth/login", json=login_data)
        print(f"   Login status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   Success: {result.get('success')}")
            print(f"   Message: {result.get('message')}")
            print(f"   Session token in response: {'session_token' in result}")
            
            if 'session_token' in result:
                session_token = result['session_token']
                print(f"   Token preview: {session_token[:10]}...")
                
                # Step 2: Test conversations API with Bearer token
                print("\n2. Testing conversations API with Bearer token...")
                headers = {
                    'Authorization': f'Bearer {session_token}',
                    'Content-Type': 'application/json'
                }
                
                conv_response = requests.get(f"{base_url}/api/conversations", headers=headers)
                print(f"   Conversations status: {conv_response.status_code}")
                print(f"   Conversations response: {conv_response.text[:200]}")
                
                # Step 3: Test conversations API with session cookies
                print("\n3. Testing conversations API with session cookies...")
                conv_response2 = session.get(f"{base_url}/api/conversations")
                print(f"   Conversations status (cookie): {conv_response2.status_code}")
                print(f"   Conversations response (cookie): {conv_response2.text[:200]}")
            
        else:
            print(f"   Login failed: {response.text}")
            
    except Exception as e:
        print(f"   Error: {e}")

if __name__ == "__main__":
    test_login_and_conversations()
