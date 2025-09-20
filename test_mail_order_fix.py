#!/usr/bin/env python3
"""
Quick test script to verify the mail order fix is working
"""

import requests
import json

def test_mail_order_fix():
    """Test specifically the mail order history fix"""
    
    print("🧪 Testing Mail Order History Fix")
    print("=" * 50)
    
    # Find server
    try:
        response = requests.get("http://127.0.0.1:8080/api/health", timeout=3)
        if response.status_code != 200:
            print("❌ Server not found on port 8080")
            return
    except:
        print("❌ Server not responding")
        return
    
    print("✅ Server found on port 8080")
    
    # Test login
    login_data = {
        "email": "john.smith@cvshealth.com", 
        "password": "password123"
    }
    
    try:
        login_response = requests.post("http://127.0.0.1:8080/api/auth/login", json=login_data)
        if login_response.status_code != 200:
            print("❌ Login failed")
            return
        
        token = login_response.json().get("access_token")
        print("✅ Login successful")
        
    except Exception as e:
        print(f"❌ Login error: {e}")
        return
    
    # Test document search directly
    headers = {"Authorization": f"Bearer {token}"}
    params = {"query": "mail order history", "limit": 3}
    
    try:
        docs_response = requests.get("http://127.0.0.1:8080/api/documents/search", 
                                   headers=headers, params=params)
        
        if docs_response.status_code == 200:
            docs = docs_response.json()
            print(f"✅ Document search working - found {len(docs)} documents")
            if docs:
                print(f"   Top result: {docs[0].get('filename', 'unknown')}")
                print(f"   Score: {docs[0].get('relevance_score', 0)}")
        else:
            print(f"❌ Document search failed: {docs_response.status_code}")
            
    except Exception as e:
        print(f"❌ Document search error: {e}")
    
    print("\n🎯 Ready to test chat!")
    print("Ask: 'How do I access a member's mail order history?'")
    print("Expected logs: '🔍 Using mail order history response'")
    print("Expected result: Enhanced response with document reference")

if __name__ == "__main__":
    test_mail_order_fix()
