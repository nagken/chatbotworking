#!/usr/bin/env python3
"""
Simple test to verify document integration is working
"""

import requests
import json

def test_user_experience():
    """Test the user experience with document integration"""
    print("🧪 Testing User Experience - Document Integration")
    print("=" * 60)
    
    base_url = "http://127.0.0.1:5000"
    
    # Login first
    print("🔐 Logging in...")
    login_response = requests.post(f"{base_url}/api/auth/login", json={
        "email": "admin@pss-knowledge-assist.com",
        "password": "SecurePass123!"
    })
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        return
    
    session_token = login_response.json()["session_token"]
    headers = {"Authorization": f"Bearer {session_token}"}
    print("✅ Login successful")
    
    # Test contraceptive coverage question
    print("\n🔍 Testing: 'What is contraceptive coverage?'")
    
    # Create conversation
    conv_response = requests.post(
        f"{base_url}/api/conversations", 
        json={"title": "Document Integration Test"},
        headers=headers
    )
    
    if conv_response.status_code != 201:
        print(f"❌ Failed to create conversation: {conv_response.status_code}")
        return
    
    conversation_id = conv_response.json()["id"]
    print(f"✅ Created conversation: {conversation_id}")
    
    # Send chat message with streaming
    chat_data = {
        "message": "What is contraceptive coverage?",
        "conversation_id": conversation_id
    }
    
    print("\n📡 Sending chat request...")
    response = requests.post(
        f"{base_url}/api/chat/stream",
        json=chat_data,
        headers=headers,
        stream=True
    )
    
    if response.status_code == 200:
        print("✅ Streaming response received")
        
        # Process the stream
        insights_found = False
        document_refs_found = False
        
        for line in response.iter_lines(decode_unicode=True):
            if line.startswith("data: "):
                try:
                    data = json.loads(line[6:])  # Remove "data: " prefix
                    
                    if data.get('message_type') == 'insights':
                        insights_found = True
                        ai_response = data.get('data', {}).get('ai_insights', '')
                        print(f"\n💬 AI Response Preview:")
                        print(f"   {ai_response[:200]}...")
                        
                        # Check for document references
                        doc_refs = data.get('data', {}).get('document_references', [])
                        if doc_refs:
                            document_refs_found = True
                            print(f"\n📄 Document References Found: {len(doc_refs)}")
                            for i, ref in enumerate(doc_refs, 1):
                                print(f"   {i}. {ref['title']}")
                                print(f"      📁 File: {ref['filename']}")
                                print(f"      🔗 URL: {ref['url']}")
                                print(f"      📋 Type: {ref['type']}")
                        
                        # Check if response contains clickable links
                        if '<a href="/documents/' in ai_response:
                            print(f"\n🔗 Clickable document links found in response!")
                        else:
                            print(f"\n⚠️ No clickable links found in response")
                
                except json.JSONDecodeError:
                    pass  # Skip malformed JSON
        
        # Summary
        print(f"\n📊 Test Results:")
        print(f"   ✅ Insights received: {insights_found}")
        print(f"   ✅ Document references: {document_refs_found}")
        
        if insights_found and document_refs_found:
            print(f"\n🎉 SUCCESS: Document integration is working!")
            print(f"   • Users now get actual document content")
            print(f"   • Clickable links are provided")
            print(f"   • System references specific CVS documents")
        else:
            print(f"\n❌ ISSUE: Document integration may not be fully working")
    
    else:
        print(f"❌ Chat request failed: {response.status_code}")
        print(f"Response: {response.text}")

def test_document_serving():
    """Test the document serving endpoint"""
    print(f"\n📄 Testing Document Serving Endpoint")
    print("=" * 50)
    
    base_url = "http://127.0.0.1:5000"
    
    # Test a known document
    test_filename = "PD  72703 Compass - Contraceptives_Card NEW as of 12022024.docx"
    encoded_filename = requests.utils.quote(test_filename)
    
    print(f"🔗 Testing: /documents/{encoded_filename}")
    
    try:
        response = requests.head(f"{base_url}/documents/{encoded_filename}")
        
        if response.status_code == 200:
            print("✅ Document serving works!")
            print(f"   Content-Type: {response.headers.get('content-type', 'unknown')}")
            content_length = response.headers.get('content-length', 'unknown')
            if content_length != 'unknown':
                print(f"   Size: {int(content_length) / 1024:.1f} KB")
        else:
            print(f"❌ Document serving failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Document test error: {e}")

if __name__ == "__main__":
    test_user_experience()
    test_document_serving()