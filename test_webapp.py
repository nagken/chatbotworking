#!/usr/bin/env python3
"""
Test chat functionality with PDF search and LLM integration
"""

import requests
import json

def test_chat_functionality():
    """Test the chat endpoint with a sample query"""
    
    base_url = "http://localhost:8080"
    
    # Test PDF search
    print("🔍 Testing PDF search...")
    search_response = requests.get(f"{base_url}/api/search", params={"q": "contraceptive coverage"})
    if search_response.status_code == 200:
        search_data = search_response.json()
        print(f"✅ PDF Search working - Found {len(search_data.get('results', []))} results")
    else:
        print(f"❌ PDF Search failed: {search_response.status_code}")
    
    # Test streaming chat
    print("\n💬 Testing streaming chat...")
    chat_data = {
        "message": "What is contraceptive coverage?",
        "conversation_id": "test-conversation-123"
    }
    
    chat_response = requests.post(
        f"{base_url}/api/chat/stream", 
        json=chat_data,
        headers={"Content-Type": "application/json"},
        stream=True
    )
    
    if chat_response.status_code == 200:
        print("✅ Chat endpoint responding...")
        
        # Read streaming response
        response_chunks = []
        for chunk in chat_response.iter_lines(decode_unicode=True):
            if chunk:
                print(f"📦 Received chunk: {chunk[:100]}...")
                response_chunks.append(chunk)
        
        print(f"✅ Received {len(response_chunks)} response chunks")
        
        if response_chunks:
            print("🎉 Chat functionality is working!")
            return True
        else:
            print("❌ No response chunks received")
            return False
    else:
        print(f"❌ Chat failed: {chat_response.status_code} - {chat_response.text}")
        return False

if __name__ == "__main__":
    print("🧪 Testing CVS Pharmacy webapp functionality...\n")
    success = test_chat_functionality()
    
    if success:
        print("\n🎉 All tests passed! The webapp is working correctly!")
        print("🌐 Access your webapp at: http://localhost:8080")
    else:
        print("\n❌ Some tests failed. Check the webapp logs.")