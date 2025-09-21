#!/usr/bin/env python3
"""
Test the document link functionality after the regex pattern fixes
"""

import requests
import json
import time

def test_chat_with_documents():
    """Test the chat endpoint to see if document links are working"""
    
    print("Testing chat with contraceptive coverage question...")
    
    url = "http://127.0.0.1:5000/api/chat"
    payload = {
        "message": "What is contraceptive coverage?",
        "conversation_id": "test_links_123"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Chat API failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
        result = response.json()
        assistant_response = result.get('assistant_response', '')
        
        print("✅ Chat API responded successfully")
        print(f"Response length: {len(assistant_response)} characters")
        
        # Check for document references in the response
        if '(Document' in assistant_response:
            print("✅ Response contains document references")
            
            # Extract document references
            import re
            doc_refs = re.findall(r'\(Document \d+: ([^)]+)\)', assistant_response)
            print(f"Found {len(doc_refs)} document references:")
            for i, ref in enumerate(doc_refs, 1):
                print(f"  {i}. {ref}")
        else:
            print("❌ No document references found in response")
            
        # Show first 500 characters of response
        print("\nResponse preview:")
        print("-" * 50)
        print(assistant_response[:500])
        if len(assistant_response) > 500:
            print("... (truncated)")
        print("-" * 50)
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing chat: {e}")
        return False

def test_streaming_endpoint():
    """Test the streaming endpoint to see document link processing"""
    
    print("\nTesting streaming endpoint...")
    
    url = "http://127.0.0.1:5000/api/chat/stream"
    payload = {
        "message": "contraceptive coverage information",
        "conversation_id": "test_stream_123"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30, stream=True)
        
        if response.status_code != 200:
            print(f"❌ Streaming API failed: {response.status_code}")
            return False
            
        print("✅ Streaming API responding...")
        
        full_response = ""
        document_links_count = 0
        
        for line in response.iter_lines():
            if line:
                line_text = line.decode('utf-8')
                if line_text.startswith('data: '):
                    try:
                        data = json.loads(line_text[6:])  # Remove 'data: ' prefix
                        
                        if data.get('type') == 'content':
                            full_response += data.get('content', '')
                        elif data.get('type') == 'document_links':
                            document_links_count = len(data.get('links', []))
                            print(f"📎 Document links received: {document_links_count}")
                            if document_links_count > 0:
                                print("Document links:")
                                for link in data.get('links', []):
                                    print(f"  - {link.get('filename', 'Unknown')}")
                        elif data.get('type') == 'done':
                            print("✅ Streaming completed")
                            break
                            
                    except json.JSONDecodeError:
                        continue
        
        print(f"\nStreaming results:")
        print(f"- Full response length: {len(full_response)} characters")
        print(f"- Document links found: {document_links_count}")
        
        if '(Document' in full_response:
            import re
            doc_refs = re.findall(r'\(Document \d+: ([^)]+)\)', full_response)
            print(f"- Document references in text: {len(doc_refs)}")
            
        return document_links_count > 0
        
    except Exception as e:
        print(f"❌ Error testing streaming: {e}")
        return False

def main():
    print("CVS Pharmacy Knowledge Assist - Document Links Test")
    print("=" * 60)
    
    # Wait a moment for server to be ready
    time.sleep(2)
    
    # Test both endpoints
    chat_ok = test_chat_with_documents()
    streaming_ok = test_streaming_endpoint()
    
    print("\n" + "=" * 60)
    print("RESULTS:")
    print(f"Chat API: {'✅' if chat_ok else '❌'}")
    print(f"Streaming with document links: {'✅' if streaming_ok else '❌'}")
    
    if streaming_ok:
        print("\n🎉 SUCCESS: Document links are working!")
    else:
        print("\n🔍 Document links still need debugging")

if __name__ == "__main__":
    main()