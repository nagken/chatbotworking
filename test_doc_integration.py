#!/usr/bin/env python3
"""Simple test to verify document search and chat response integration."""

import requests
import json
import time

# Test the API directly
def test_document_search_api():
    """Test the document search API directly"""
    print("🔍 Testing Document Search API...")
    
    url = "http://127.0.0.1:8080/api/documents/search"
    params = {"query": "mail order history"}
    
    try:
        response = requests.get(url, params=params)
        print(f"📈 Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📊 Results found: {len(data.get('results', []))}")
            
            for i, result in enumerate(data.get('results', [])[:3]):
                print(f"  {i+1}. {result.get('filename', 'Unknown')}")
                print(f"     Score: {result.get('relevance_score', 0)}")
                print(f"     Snippet: {result.get('snippet', '')[:100]}...")
                print()
            
            return len(data.get('results', [])) > 0
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def test_login():
    """Test login to get session token"""
    print("🔐 Testing Login...")
    
    url = "http://127.0.0.1:8080/api/auth/login"
    payload = {
        "email": "demo@cvs-pharmacy-knowledge-assist.com",
        "password": "demo1234"
    }
    
    try:
        response = requests.post(url, json=payload)
        print(f"📈 Login Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and data.get("token"):
                print(f"✅ Login successful!")
                return data["token"]
            else:
                print(f"❌ Login failed: {data.get('message')}")
                return None
        else:
            print(f"❌ Login error: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Login exception: {e}")
        return None

def test_chat_with_auth(token):
    """Test chat endpoint with authentication"""
    print("💬 Testing Chat with Authentication...")
    
    url = "http://127.0.0.1:8080/api/chat"
    payload = {
        "message": "How do I access a member's mail order history?",
        "conversation_id": f"test_{int(time.time())}"
    }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        print(f"📈 Chat Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            response_text = data.get("assistant_response", "")
            
            print(f"📝 Response Length: {len(response_text)} characters")
            print(f"📚 Contains 'Related Documents': {'Related Documents' in response_text}")
            print(f"📄 Contains document emoji: {'📚' in response_text}")
            print(f"📦 Contains 'mail order': {'mail order' in response_text.lower()}")
            
            print("\n📄 Response Preview:")
            print("-" * 50)
            print(response_text[:500] + "..." if len(response_text) > 500 else response_text)
            print("-" * 50)
            
            return "Related Documents" in response_text
        else:
            print(f"❌ Chat error: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Chat exception: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 CVS Pharmacy Document Search Integration Test")
    print("=" * 60)
    
    # Test 1: Document Search API (no auth required)
    doc_search_works = test_document_search_api()
    print()
    
    # Test 2: Login
    token = test_login()
    print()
    
    if token:
        # Test 3: Chat with document integration
        chat_works = test_chat_with_auth(token)
        print()
        
        print("=" * 60)
        print("📊 TEST SUMMARY:")
        print(f"  📄 Document Search API: {'✅ PASS' if doc_search_works else '❌ FAIL'}")
        print(f"  🔐 Authentication: {'✅ PASS' if token else '❌ FAIL'}")
        print(f"  💬 Chat Integration: {'✅ PASS' if chat_works else '❌ FAIL'}")
        print("=" * 60)
        
        if doc_search_works and token and chat_works:
            print("🎉 ALL TESTS PASSED! Document search integration is working!")
        else:
            print("⚠️  Some tests failed. Check the output above for details.")
    else:
        print("❌ Cannot proceed without authentication")

if __name__ == "__main__":
    main()
