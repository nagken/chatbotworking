#!/usr/bin/env python3
"""
Test script to verify clear conversations functionality with proper authentication
"""

import requests
import json

def test_with_proper_auth():
    base_url = "http://127.0.0.1:5000"
    
    print("🧪 Testing Clear All Conversations with authentication...")
    
    # Step 1: Check if server is running
    try:
        health_response = requests.get(f"{base_url}/api/health", timeout=5)
        print(f"✅ Server health check: {health_response.status_code}")
    except Exception as e:
        print(f"❌ Server not accessible: {e}")
        return
    
    # Step 2: Try to get a session token (like the frontend does)
    session = requests.Session()
    
    try:
        # First, visit the main page to establish a session
        main_page = session.get(f"{base_url}/", timeout=5)
        print(f"✅ Main page loaded: {main_page.status_code}")
        
        # Check if we can access conversations endpoint with session
        conversations_response = session.get(f"{base_url}/api/conversations", timeout=5)
        print(f"Conversations endpoint status: {conversations_response.status_code}")
        
        if conversations_response.status_code == 200:
            print("✅ Authentication working with session")
            
            # Now try to clear conversations
            clear_response = session.delete(f"{base_url}/api/conversations/clear-all", timeout=10)
            print(f"Clear conversations status: {clear_response.status_code}")
            
            if clear_response.status_code == 200:
                result = clear_response.json()
                print(f"✅ Clear conversations successful: {result}")
            else:
                print(f"❌ Clear conversations failed: {clear_response.text}")
                
        elif conversations_response.status_code == 401:
            print("❌ Authentication still required")
        else:
            print(f"❌ Unexpected status: {conversations_response.status_code}")
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")

if __name__ == "__main__":
    test_with_proper_auth()