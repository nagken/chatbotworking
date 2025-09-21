#!/usr/bin/env python3

import requests
import json

def test_document_api():
    """Test the actual document API endpoints"""
    
    session = requests.Session()
    
    # Login
    login_data = {"email": "admin@pss-knowledge-assist.com", "password": "admin123"}
    login_response = session.post("http://127.0.0.1:5000/api/auth/login", json=login_data)
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        return
        
    print("✅ Login successful")
    
    # Test API endpoints
    endpoints = [
        "/api/documents/search?query=contraceptive",
        "/api/documents/stats",
        "/api/documents/categories"
    ]
    
    for endpoint in endpoints:
        print(f"\n🔍 Testing: {endpoint}")
        try:
            response = session.get(f"http://127.0.0.1:5000{endpoint}", timeout=10)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if 'results' in data:
                    print(f"Results: {len(data.get('results', []))}")
                    if data.get('results'):
                        first_result = data['results'][0]
                        print(f"First result: {first_result.get('filename', 'No filename')}")
                elif 'categories' in data:
                    print(f"Categories: {data.get('categories', [])}")
                elif 'total_documents' in data:
                    print(f"Total documents: {data.get('total_documents', 0)}")
                else:
                    print(f"Response keys: {list(data.keys())}")
            else:
                print(f"Error: {response.text}")
                
        except Exception as e:
            print(f"Exception: {e}")

if __name__ == "__main__":
    test_document_api()