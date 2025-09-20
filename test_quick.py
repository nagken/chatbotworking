#!/usr/bin/env python3
"""
Quick server connectivity test
"""

import requests

def quick_test():
    print("🏥 CVS Pharmacy Knowledge Assist - Quick Connectivity Test")
    print("=" * 50)
    
    base_url = "http://localhost:5000"
    
    # Test 1: Basic health check
    print("1. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/api/health", timeout=5)
        print(f"   Health Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 2: Main page
    print("\n2. Testing main page...")
    try:
        response = requests.get(base_url, timeout=5)
        print(f"   Main page Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Main page accessible")
        else:
            print(f"   Error: {response.text[:100]}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 3: Login endpoint (should return 422 without data)
    print("\n3. Testing login endpoint...")
    try:
        response = requests.post(f"{base_url}/api/auth/login", timeout=5)
        print(f"   Login Status: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 4: Document search (should return 422 without query)
    print("\n4. Testing document search...")
    try:
        response = requests.get(f"{base_url}/api/documents/search", timeout=5)
        print(f"   Search Status: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n" + "=" * 50)
    print("Quick test completed!")

if __name__ == "__main__":
    quick_test()
