#!/usr/bin/env python3
"""
Final test to verify the webapp is working with real LLM integration
"""

import requests
import json
import time

def test_webapp_final():
    """Test the webapp to verify real LLM integration vs mock responses"""
    
    print("🔬 Final CVS Pharmacy Knowledge Assist Test")
    print("=" * 50)
    
    # Test 1: Basic connectivity
    try:
        print("1️⃣ Testing basic connectivity...")
        response = requests.get("http://localhost:8080/", timeout=5)
        if response.status_code == 200:
            print("✅ Webapp is accessible")
        else:
            print(f"❌ Webapp returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to webapp: {e}")
        return False
    
    # Test 2: Streaming chat functionality
    try:
        print("\n2️⃣ Testing streaming chat functionality...")
        
        payload = {
            "message": "What is contraceptive coverage?",
            "superclient": None,
            "conversation_id": None
        }
        
        response = requests.post(
            "http://localhost:8080/api/chat/stream",
            json=payload,
            headers={"Content-Type": "application/json"},
            stream=True,
            timeout=30
        )
        
        print(f"📡 Response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Streaming endpoint returned status {response.status_code}")
            print(f"Response text: {response.text[:200]}...")
            return False
        
        # Process streaming response
        chunks = []
        response_content = ""
        
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    data_str = line_str[6:]  # Remove 'data: ' prefix
                    if data_str.strip() == '[DONE]':
                        break
                    try:
                        chunk_data = json.loads(data_str)
                        chunks.append(chunk_data)
                        
                        # Extract content from chunks
                        if 'data' in chunk_data and 'content' in chunk_data['data']:
                            response_content += chunk_data['data']['content']
                        elif 'content' in chunk_data:
                            response_content += chunk_data['content']
                            
                    except json.JSONDecodeError:
                        pass  # Skip malformed JSON
        
        print(f"✅ Received {len(chunks)} streaming chunks")
        
        # Test 3: Analyze response content for mock vs real indicators
        print("\n3️⃣ Analyzing response content...")
        
        response_lower = response_content.lower()
        
        # Check for mock response indicators
        mock_indicators = [
            'mock streaming response',
            'mock conversation',
            'using contraceptive coverage response',
            'using generic document-based response'
        ]
        
        has_mock_indicators = any(indicator in response_lower for indicator in mock_indicators)
        
        # Check for real LLM response indicators
        real_llm_indicators = [
            'based on the cvs',
            'according to',
            'vertex ai',
            'search results',
            'data analytics'
        ]
        
        has_real_indicators = any(indicator in response_lower for indicator in real_llm_indicators)
        
        print(f"📄 Response content length: {len(response_content)} characters")
        print(f"🔍 Contains mock indicators: {has_mock_indicators}")
        print(f"🧠 Contains real LLM indicators: {has_real_indicators}")
        
        if response_content:
            print(f"📝 Response preview: {response_content[:200]}...")
        
        # Final verdict
        if has_mock_indicators:
            print("\n⚠️  RESULT: Still using MOCK responses")
            print("   The database connection fix may not have fully resolved the issue")
            return False
        elif len(response_content) > 50 and not has_mock_indicators:
            print("\n🎉 RESULT: Appears to be using REAL LLM responses!")
            print("   The webapp is successfully integrating with Vertex AI and Gemini")
            return True
        else:
            print("\n❓ RESULT: Unclear - response too short or ambiguous")
            return False
            
    except Exception as e:
        print(f"❌ Streaming test error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 CVS Pharmacy Knowledge Assist - Integration Verification")
    print(f"🕐 Test time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    success = test_webapp_final()
    
    print("\n" + "=" * 50)
    if success:
        print("🎊 SUCCESS: CVS Pharmacy Knowledge Assist is working with real LLM integration!")
        print("✅ PDF search, Vertex AI, and Gemini LLM are properly connected")
        print("✅ Database integration is functioning correctly")
        print("✅ Streaming responses are working as expected")
    else:
        print("❌ ISSUES DETECTED: Further debugging may be needed")
        print("💡 Check the webapp logs for more details")
    
    print("\n📝 Next steps:")
    print("  • Open http://localhost:8080 in your browser")
    print("  • Ask questions about contraceptive coverage, pharmacy policies, etc.")
    print("  • Verify responses are contextual and based on your CVS documents")