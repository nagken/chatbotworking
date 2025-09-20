#!/usr/bin/env python3
"""
Check if the server is running and test basic endpoints
"""
import requests
import time

def check_server():
    """Check if server is running"""
    base_url = "http://127.0.0.1:8080"
    
    # Test endpoints
    endpoints = [
        "/health",
        "/api/health", 
        "/test-login",
        "/"
    ]
    
    print(f"Checking server at {base_url}...")
    
    for endpoint in endpoints:
        url = f"{base_url}{endpoint}"
        try:
            response = requests.get(url, timeout=5)
            print(f"✅ {endpoint}: {response.status_code}")
            if endpoint == "/health" or endpoint == "/api/health":
                print(f"   Response: {response.text[:100]}")
        except requests.exceptions.ConnectionError:
            print(f"❌ {endpoint}: Connection refused (server not running?)")
        except Exception as e:
            print(f"❌ {endpoint}: {e}")
            
    # Test login endpoint
    print("\nTesting login endpoint...")
    try:
        login_data = {
            "email": "admin@pss-knowledge-assist.com",
            "password": "admin123",
            "remember_me": False
        }
        response = requests.post(f"{base_url}/api/auth/login", json=login_data, timeout=5)
        print(f"✅ Login test: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   Success: {result.get('success')}")
            print(f"   Message: {result.get('message')}")
    except Exception as e:
        print(f"❌ Login test failed: {e}")

if __name__ == "__main__":
    check_server()
