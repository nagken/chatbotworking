#!/usr/bin/env python3
"""
Test the clear conversations endpoint directly
"""
import requests
import json

def test_clear_conversations():
    print("🧪 Testing Clear Conversations Endpoint")
    print("=" * 50)
    
    base_url = "http://127.0.0.1:5000"
    
    # First, try to get a session/login
    print("1. Testing login...")
    try:
        login_response = requests.post(f"{base_url}/api/auth/login", 
                                     json={"email": "test@cvs.com", "password": "test123"},
                                     timeout=10)
        print(f"   Login status: {login_response.status_code}")
        
        if login_response.status_code == 200:
            login_data = login_response.json()
            token = login_data.get('access_token')
            print(f"   Token received: {token[:20] if token else 'None'}...")
            
            # Now test clear conversations
            print("\n2. Testing clear conversations...")
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            clear_response = requests.delete(f"{base_url}/api/conversations/clear-all",
                                           headers=headers,
                                           timeout=10)
            
            print(f"   Clear status: {clear_response.status_code}")
            print(f"   Clear response: {clear_response.text}")
            
            if clear_response.status_code == 200:
                print("✅ Clear conversations endpoint works!")
            else:
                print("❌ Clear conversations failed")
                
        else:
            print("❌ Login failed, testing without auth...")
            # Try without authentication (fallback mode)
            clear_response = requests.delete(f"{base_url}/api/conversations/clear-all", timeout=10)
            print(f"   Clear status (no auth): {clear_response.status_code}")
            print(f"   Clear response: {clear_response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_clear_conversations()