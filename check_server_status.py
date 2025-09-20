#!/usr/bin/env python3
"""
Quick server status check script
"""

import requests
import sys

def check_server():
    ports = [8000, 8080]
    
    for port in ports:
        try:
            url = f"http://localhost:{port}"
            print(f"Checking {url}...")
            
            response = requests.get(url, timeout=5)
            print(f"✅ Server is running on port {port}")
            print(f"Status Code: {response.status_code}")
            
            # Test health endpoint
            health_url = f"{url}/api/health"
            health_response = requests.get(health_url, timeout=5)
            print(f"✅ Health endpoint: {health_response.status_code}")
            
            # Test document search
            search_url = f"{url}/api/documents/search?query=test"
            search_response = requests.get(search_url, timeout=5)
            print(f"✅ Search endpoint: {search_response.status_code}")
            
            return port
            
        except requests.exceptions.RequestException as e:
            print(f"❌ No server on port {port}: {e}")
    
    print("❌ No server found on any port")
    return None

if __name__ == "__main__":
    active_port = check_server()
    if active_port:
        print(f"\n🎉 Server is active on port {active_port}")
        print(f"Main URL: http://localhost:{active_port}")
        print(f"Health: http://localhost:{active_port}/api/health")
        print(f"Search: http://localhost:{active_port}/api/documents/search?query=test")
    else:
        print("\n❌ Server needs to be started")
        print("Run: python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload")
