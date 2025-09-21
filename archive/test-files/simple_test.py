#!/usr/bin/env python3
"""Simple test to verify the CVS Pharmacy document search is working."""

import requests
import json

def test_health():
    """Test if server is running"""
    try:
        response = requests.get("http://127.0.0.1:8001/api/health", timeout=5)
        print(f"🏥 Health Check: {response.status_code}")
        if response.status_code == 200:
            print(f"✅ Server is running!")
            return True
        else:
            print(f"❌ Server not healthy: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Server not reachable: {e}")
        return False

def test_documents():
    """Test document search API"""
    try:
        response = requests.get("http://127.0.0.1:8001/api/documents/search?query=mail+order+history", timeout=10)
        print(f"📄 Document Search: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            print(f"✅ Found {len(results)} documents")
            
            for i, doc in enumerate(results[:3]):
                print(f"  {i+1}. {doc.get('filename', 'Unknown')}")
                print(f"     Score: {doc.get('relevance_score', 0)}")
                print(f"     Snippet: {doc.get('snippet', '')[:100]}...")
                print()
            
            return len(results) > 0
        else:
            print(f"❌ Document search failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Document search error: {e}")
        return False

def test_login():
    """Test login functionality"""
    try:
        payload = {
            "email": "demo@cvs-pharmacy-knowledge-assist.com",
            "password": "demo1234"
        }
        response = requests.post("http://127.0.0.1:8001/api/auth/login", json=payload, timeout=10)
        print(f"🔐 Login Test: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and data.get("token"):
                print(f"✅ Login successful!")
                return data["token"]
            else:
                print(f"❌ Login failed: {data.get('message', 'Unknown error')}")
                return None
        else:
            print(f"❌ Login request failed: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def test_chat(token):
    """Test chat functionality with authentication"""
    try:
        payload = {
            "message": "How do I access a member's mail order history?",
            "conversation_id": "test_12345"
        }
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        response = requests.post("http://127.0.0.1:8001/api/chat", json=payload, headers=headers, timeout=15)
        print(f"💬 Chat Test: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            response_text = data.get("assistant_response", "")
            
            print(f"📝 Response length: {len(response_text)} characters")
            
            # Check for document content
            has_related_docs = "Related Documents" in response_text
            has_doc_emoji = "📚" in response_text
            has_mail_order = "mail order" in response_text.lower()
            
            print(f"📚 Contains 'Related Documents': {'✅' if has_related_docs else '❌'}")
            print(f"📄 Contains document emoji: {'✅' if has_doc_emoji else '❌'}")
            print(f"📦 Contains 'mail order': {'✅' if has_mail_order else '❌'}")
            
            if has_related_docs:
                print("🎉 SUCCESS: Document integration is working!")
                print("\n📝 Response preview:")
                print("-" * 50)
                print(response_text[:500] + "..." if len(response_text) > 500 else response_text)
                print("-" * 50)
                return True
            else:
                print("⚠️ WARNING: No document section found in response")
                print("\n📝 Actual response:")
                print("-" * 50)
                print(response_text)
                print("-" * 50)
                return False
        else:
            print(f"❌ Chat request failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Chat error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 CVS Pharmacy Knowledge Assist - Document Search Test")
    print("=" * 60)
    
    # Test 1: Health check
    if not test_health():
        print("❌ Server is not running. Please start the server first.")
        return
    
    print()
    
    # Test 2: Document search (no auth required)
    doc_works = test_documents()
    print()
    
    # Test 3: Login
    token = test_login()
    print()
    
    if token:
        # Test 4: Chat with document integration
        chat_works = test_chat(token)
        print()
        
        # Summary
        print("=" * 60)
        print("📊 FINAL RESULTS:")
        print(f"  🏥 Server Health: ✅ PASS")
        print(f"  📄 Document Search: {'✅ PASS' if doc_works else '❌ FAIL'}")
        print(f"  🔐 Authentication: {'✅ PASS' if token else '❌ FAIL'}")
        print(f"  💬 Chat Integration: {'✅ PASS' if chat_works else '❌ FAIL'}")
        print("=" * 60)
        
        if doc_works and chat_works:
            print("🎉 ALL TESTS PASSED! Document search is working correctly!")
            print("\n🔍 To test in the browser:")
            print("   1. Go to: http://127.0.0.1:8001/static/index.html")
            print("   2. Login with: demo@cvs-pharmacy-knowledge-assist.com / demo1234")
            print("   3. Ask: 'How do I access a member's mail order history?'")
            print("   4. You should see a '📚 Related Documents Found:' section")
        else:
            print("❌ Some tests failed. Check the output above for details.")
    else:
        print("❌ Cannot test chat without authentication")

if __name__ == "__main__":
    main()
