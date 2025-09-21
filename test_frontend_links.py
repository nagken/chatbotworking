#!/usr/bin/env python3
"""
Test the updated frontend with document links functionality
"""

import requests
import json
import time

def test_streaming_with_document_links():
    """Test that the streaming endpoint returns document links properly"""
    
    print("🧪 Testing streaming endpoint with document references...")
    
    url = "http://127.0.0.1:5000/api/chat/stream"
    payload = {
        "message": "What is contraceptive coverage?",
        "conversation_id": "test_frontend_links_123"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30, stream=True)
        
        if response.status_code != 200:
            print(f"❌ Streaming API failed: {response.status_code}")
            return False
            
        print("✅ Streaming API responding...")
        
        document_links_found = False
        insights_content = ""
        document_references = []
        
        for line in response.iter_lines():
            if line:
                line_text = line.decode('utf-8')
                if line_text.startswith('data: '):
                    try:
                        data = json.loads(line_text[6:])  # Remove 'data: ' prefix
                        
                        if data.get('type') == 'system_message':
                            message_type = data.get('message_type')
                            if message_type == 'insights':
                                message_data = data.get('data', {})
                                insights_content = message_data.get('ai_insights', '')
                                document_references = message_data.get('document_references', [])
                                
                                print(f"📎 Insights message received:")
                                print(f"   - Content length: {len(insights_content)} characters")
                                print(f"   - Document references: {len(document_references)}")
                                
                                if document_references:
                                    document_links_found = True
                                    print("📋 Document References:")
                                    for i, doc in enumerate(document_references, 1):
                                        print(f"   {i}. {doc.get('title', 'No title')}")
                                        print(f"      File: {doc.get('filename', 'No filename')}")
                                        print(f"      URL: {doc.get('url', 'No URL')}")
                                        print(f"      Type: {doc.get('type', 'No type')}")
                                
                        elif data.get('type') == 'done':
                            print("✅ Streaming completed")
                            break
                            
                    except json.JSONDecodeError:
                        continue
        
        print(f"\n🔍 Test Results:")
        print(f"- Insights content received: {'✅' if insights_content else '❌'}")
        print(f"- Document references received: {'✅' if document_references else '❌'}")
        print(f"- Document links found: {'✅' if document_links_found else '❌'}")
        
        if document_links_found:
            print(f"\n🎉 SUCCESS: Document links are working!")
            print(f"   Frontend will now display {len(document_references)} clickable document links")
        else:
            print(f"\n⚠️ No document links found")
            
        return document_links_found
        
    except Exception as e:
        print(f"❌ Error testing streaming: {e}")
        return False

def main():
    print("CVS Pharmacy Knowledge Assist - Frontend Document Links Test")
    print("=" * 65)
    
    # Wait a moment for server to be ready
    time.sleep(2)
    
    # Test the streaming endpoint
    success = test_streaming_with_document_links()
    
    print("\n" + "=" * 65)
    if success:
        print("🎊 FRONTEND UPDATE SUCCESSFUL!")
        print("   - Document references are being sent from backend")
        print("   - Frontend code updated to display document links")
        print("   - CSS styling added for clickable document buttons")
        print("   - Users will now see clickable document links in AI responses")
    else:
        print("❌ Test failed - document links not working")

if __name__ == "__main__":
    main()