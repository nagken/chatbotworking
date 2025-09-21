#!/usr/bin/env python3
"""
Simple test of the clear conversations endpoint
"""

import requests
import json

def test_simple_clear():
    base_url = "http://127.0.0.1:5000"
    
    print("🧪 Simple Clear Test")
    print("=" * 30)
    
    # Test direct API call
    try:
        print("Testing clear conversations endpoint...")
        response = requests.delete(f"{base_url}/api/conversations/clear-all", timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("Test complete!")

if __name__ == "__main__":
    test_simple_clear()