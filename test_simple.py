#!/usr/bin/env python3
"""
Simple test to verify LLM integration is working
"""

import requests
import json

def test_webapp_simple():
    """Simple test to verify webapp LLM vs mock responses"""
    
    print("🧪 Testing webapp LLM integration...")
    
    try:
        # Test streaming chat endpoint
        response = requests.post(
            "http://localhost:8080/api/chat/stream",
            json={"message": "What is contraceptive coverage?"},
            headers={"Content-Type": "application/json"},
            stream=True,
            timeout=30
        )
        
        print(f"📡 Response status: {response.status_code}")
        
        if response.status_code == 200:
            chunks = []
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]
                        if data_str.strip() == '[DONE]':
                            break
                        try:
                            data = json.loads(data_str)
                            chunks.append(data)
                            print(f"📨 Chunk: {data.get('type', 'unknown')} - {str(data)[:100]}...")
                        except json.JSONDecodeError:
                            pass
            
            print(f"\n✅ Received {len(chunks)} chunks")
            
            # Check for mock vs real LLM indicators
            has_mock_indicators = any(
                'mock' in str(chunk).lower() or 
                'contraceptive coverage response' in str(chunk).lower()
                for chunk in chunks
            )
            
            if has_mock_indicators:
                print("⚠️ Still using MOCK responses")
                return False
            else:
                print("🎉 Appears to be using REAL LLM responses!")
                return True
        else:
            print(f"❌ Request failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

if __name__ == "__main__":
    success = test_webapp_simple()
    if success:
        print("\n✅ LLM integration appears to be working!")
    else:
        print("\n❌ Still using mock responses - need to debug further")