#!/usr/bin/env python3
"""
Test script to verify conversation mock endpoints work correctly
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def test_conversations():
    """Test the conversations endpoints with mock fallback"""
    
    print("🧪 Testing PSS Knowledge Assist - Conversation Mock Endpoints")
    print("=" * 60)
    
    # Test login first
    print("\n1. Testing login...")
    login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "admin@pss-knowledge-assist.com",
        "password": "admin123"
    })
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        return False
    
    token = login_response.json().get("access_token")
    if not token:
        print("❌ No access token received")
        return False
    
    print(f"✅ Login successful, token: {token[:20]}...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test conversation list
    print("\n2. Testing conversation list...")
    conversations_response = requests.get(f"{BASE_URL}/api/conversations", headers=headers)
    
    if conversations_response.status_code != 200:
        print(f"❌ Conversations failed: {conversations_response.status_code}")
        return False
    
    conversations_data = conversations_response.json()
    conversations = conversations_data.get("conversations", [])
    print(f"✅ Found {len(conversations)} conversations")
    
    if conversations:
        for i, conv in enumerate(conversations[:2]):  # Test first 2
            print(f"   {i+1}. {conv['title']} (ID: {conv['id'][:8]}...)")
    
    # Test conversation messages
    if conversations:
        print("\n3. Testing conversation messages...")
        first_conv_id = conversations[0]["id"]
        messages_response = requests.get(f"{BASE_URL}/api/conversations/{first_conv_id}/messages", headers=headers)
        
        if messages_response.status_code != 200:
            print(f"❌ Messages failed: {messages_response.status_code}")
            return False
        
        messages_data = messages_response.json()
        messages = messages_data.get("messages", [])
        print(f"✅ Found {len(messages)} messages in conversation")
        
        for i, msg in enumerate(messages[:3]):  # Show first 3
            msg_type = msg["message_type"]
            content_preview = msg["content"][:50] + "..." if len(msg["content"]) > 50 else msg["content"]
            print(f"   {i+1}. [{msg_type}] {content_preview}")
    
    # Test conversation creation
    print("\n4. Testing conversation creation...")
    create_response = requests.post(f"{BASE_URL}/api/conversations", 
                                   headers=headers,
                                   json={"title": "Test Conversation"})
    
    if create_response.status_code != 200:
        print(f"❌ Create conversation failed: {create_response.status_code}")
        return False
    
    new_conv = create_response.json()
    print(f"✅ Created new conversation: {new_conv['title']} (ID: {new_conv['id'][:8]}...)")
    
    print("\n🎉 All conversation mock endpoints working correctly!")
    return True

if __name__ == "__main__":
    try:
        success = test_conversations()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        sys.exit(1)
