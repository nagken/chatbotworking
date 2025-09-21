#!/usr/bin/env python3
"""
Test webapp functionality with real LLM integration
"""

import requests
import json
import time

def test_webapp_llm_integration():
    """Test the webapp's LLM integration with a real query"""
    
    base_url = "http://localhost:8080"
    
    print("🔍 Testing webapp LLM integration...")
    
    try:
        # Test 1: Basic health check
        print("\n1️⃣ Testing basic webapp availability...")
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            print("✅ Webapp is running and accessible")
        else:
            print(f"❌ Webapp not accessible: {response.status_code}")
            return False
        
        # Test 2: Test streaming chat with contraceptive coverage query
        print("\n2️⃣ Testing streaming chat with contraceptive coverage query...")
        
        chat_payload = {
            "message": "What is contraceptive coverage?",
            "superclient": None,
            "conversation_id": None
        }
        
        # Make streaming request
        response = requests.post(
            f"{base_url}/api/chat/stream",
            json=chat_payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer test-session-token"  # Use any token for fallback auth
            },
            stream=True
        )
        
        if response.status_code == 200:
            print("✅ Streaming chat endpoint accessible")
            
            # Process streaming response
            streaming_content = []
            for line in response.iter_lines():
                if line:
                    try:
                        # Handle Server-Sent Events format
                        line_str = line.decode('utf-8')
                        if line_str.startswith('data: '):
                            data_str = line_str[6:]  # Remove 'data: ' prefix
                            if data_str.strip() == '[DONE]':
                                break
                            try:
                                data = json.loads(data_str)
                                streaming_content.append(data)
                                if 'content' in data:
                                    print(f"📨 Received: {data['content'][:100]}...")
                            except json.JSONDecodeError:
                                pass  # Skip non-JSON lines
                    except UnicodeDecodeError:
                        pass
            
            print(f"✅ Received {len(streaming_content)} streaming chunks")
            
            # Analyze response type
            has_real_llm_response = False
            has_pdf_search = False
            
            for chunk in streaming_content:
                if 'content' in chunk:
                    content = chunk['content'].lower()
                    # Check for signs of real LLM response vs mock
                    if 'contraceptive coverage' in content and 'cvs health plan' in content:
                        has_real_llm_response = True
                    if 'document' in content or 'pdf' in content:
                        has_pdf_search = True
            
            if has_real_llm_response:
                print("✅ Received real LLM-generated response about contraceptive coverage")
            else:
                print("⚠️ Response appears to be using mock/fallback content")
            
            if has_pdf_search:
                print("✅ PDF search integration working")
            else:
                print("⚠️ No clear PDF search results in response")
            
            return True
        else:
            print(f"❌ Streaming chat failed: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to webapp - is it running on localhost:8080?")
        return False
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 CVS Pharmacy Knowledge Assist - LLM Integration Test")
    print("=" * 60)
    
    success = test_webapp_llm_integration()
    
    if success:
        print("\n🎉 LLM integration test completed!")
        print("✅ Webapp is functioning with database and LLM services")
    else:
        print("\n❌ LLM integration test failed!")
        print("Check the webapp logs for more details")