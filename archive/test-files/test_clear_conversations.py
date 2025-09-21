#!/usr/bin/env python3
"""
Test script for the Clear All Conversations functionality
"""

import requests
import json

def test_clear_conversations():
    base_url = "http://127.0.0.1:5000"
    
    print("🧪 Testing Clear All Conversations functionality...")
    
    # Test 1: Check if server is running
    try:
        health_response = requests.get(f"{base_url}/api/health", timeout=5)
        print(f"✅ Server health check: {health_response.status_code}")
    except Exception as e:
        print(f"❌ Server not accessible: {e}")
        return
    
    # Test 2: Try to access the clear conversations endpoint
    try:
        print("\n🔍 Testing clear conversations endpoint...")
        response = requests.delete(
            f"{base_url}/api/conversations/clear-all",
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success: {result}")
        elif response.status_code == 401:
            print("❌ Authentication required - this is likely the issue!")
            print("Response:", response.text)
        elif response.status_code == 404:
            print("❌ Endpoint not found - routing issue")
            print("Response:", response.text)
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            print("Response:", response.text)
            
    except Exception as e:
        print(f"❌ Error calling clear conversations: {e}")
    
    # Test 3: Check if conversations endpoint is working
    try:
        print("\n🔍 Testing conversations list endpoint...")
        response = requests.get(f"{base_url}/api/conversations", timeout=5)
        print(f"Conversations endpoint status: {response.status_code}")
        if response.status_code == 401:
            print("❌ Authentication required for conversations too!")
        elif response.status_code == 200:
            print("✅ Conversations endpoint works")
    except Exception as e:
        print(f"❌ Error calling conversations: {e}")

if __name__ == "__main__":
    test_clear_conversations()