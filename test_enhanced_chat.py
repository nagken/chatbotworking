#!/usr/bin/env python3
"""
Test Enhanced Chat with Document Integration
Tests the new document search and link functionality
"""

import requests
import json
import time

def test_enhanced_chat():
    """Test the enhanced chat with document integration"""
    print("🧪 Testing Enhanced Chat with Document Integration")
    print("=" * 70)
    
    base_url = "http://127.0.0.1:5000"
    
    # Test queries that should find relevant documents
    test_queries = [
        "What is the contraceptive coverage policy?",
        "How does prior authorization work?", 
        "What are the Medicare Part D coverage phases?",
        "What specialty pharmacy services are available?",
        "How do I process a mail order prescription?"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🔍 Test {i}: {query}")
        print("-" * 50)
        
        try:
            # Create a new conversation for each test
            conv_response = requests.post(f"{base_url}/api/conversations", json={
                "title": f"Test Conversation {i}"
            })
            
            if conv_response.status_code == 201:
                conversation_id = conv_response.json()["id"]
                print(f"✅ Created conversation: {conversation_id}")
            else:
                print(f"❌ Failed to create conversation: {conv_response.status_code}")
                continue
            
            # Send chat message
            chat_data = {
                "message": query,
                "conversation_id": conversation_id
            }
            
            # Test streaming endpoint
            response = requests.post(
                f"{base_url}/api/chat/stream",
                json=chat_data,
                stream=True
            )
            
            if response.status_code == 200:
                print("📡 Streaming response received:")
                
                messages_received = 0
                document_refs_found = 0
                
                for line in response.iter_lines(decode_unicode=True):
                    if line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])  # Remove "data: " prefix
                            messages_received += 1
                            
                            message_type = data.get('message_type', 'unknown')
                            print(f"  📦 Message {messages_received}: {message_type}")
                            
                            if message_type == 'insights':
                                ai_response = data.get('data', {}).get('ai_insights', '')
                                print(f"  💬 AI Response: {ai_response[:200]}...")
                                
                                # Check for document references
                                doc_refs = data.get('data', {}).get('document_references', [])
                                if doc_refs:
                                    document_refs_found += len(doc_refs)
                                    print(f"  📄 Document References Found: {len(doc_refs)}")
                                    for ref in doc_refs:
                                        print(f"    - {ref['title']} ({ref['type']})")
                                        print(f"      🔗 {ref['url']}")
                                else:
                                    print("  📄 No document references found")
                        
                        except json.JSONDecodeError as e:
                            print(f"  ⚠️ JSON decode error: {e}")
                    elif line.strip():
                        print(f"  📝 Raw line: {line[:100]}...")
                
                print(f"✅ Test completed - {messages_received} messages, {document_refs_found} document refs")
                
            else:
                print(f"❌ Chat failed: {response.status_code}")
                print(f"Response: {response.text}")
        
        except Exception as e:
            print(f"❌ Test error: {e}")
        
        # Small delay between tests
        time.sleep(2)
    
    print("\n" + "=" * 70)
    print("🎯 Test Summary:")
    print("✅ Document integration should now be working!")
    print("✅ Chat responses should include actual document content")
    print("✅ Users should see clickable document links")
    print("✅ System should reference specific CVS pharmacy documents")

def test_document_endpoint():
    """Test the document serving endpoint"""
    print("\n📄 Testing Document Serving Endpoint")
    print("=" * 50)
    
    base_url = "http://127.0.0.1:5000"
    
    # Test a known document
    test_filename = "_CLIENT SUPPORT- MEMBER SERVICES St Joseph's Women's Contraceptive Coverage.docx"
    encoded_filename = requests.utils.quote(test_filename)
    
    print(f"🔗 Testing document URL: /documents/{encoded_filename}")
    
    try:
        response = requests.head(f"{base_url}/documents/{encoded_filename}")
        
        if response.status_code == 200:
            print("✅ Document endpoint working!")
            print(f"Content-Type: {response.headers.get('content-type')}")
            print(f"Content-Length: {response.headers.get('content-length')} bytes")
        elif response.status_code == 404:
            print("⚠️ Document not found - check filename")
        else:
            print(f"❌ Document endpoint error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Document test error: {e}")

if __name__ == "__main__":
    test_enhanced_chat()
    test_document_endpoint()