#!/usr/bin/env python3
"""
Test script for local search functionality without Vertex AI
"""

import requests
import json

def test_local_search():
    """Test the local search endpoint"""
    
    base_url = "http://localhost:5000"
    
    # Test questions for different patterns
    test_questions = [
        "What is the Pharmacy coverage?",
        "How do I submit a claim?", 
        "Tell me about mail order pharmacy",
        "What are the contraceptive benefits?",
        "How do I find a participating provider?",
        "What should I do if my claim is denied?",
        "random question that doesn't match any pattern"
    ]
    
    print("🧪 Testing Local Search Functionality")
    print("=" * 50)
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n{i}. Testing: '{question}'")
        print("-" * 40)
        
        try:
            # Test non-streaming endpoint
            response = requests.post(
                f"{base_url}/api/chat/local",
                json={
                    "message": question,
                    "session_token": "test_session_123"
                },
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Status: {response.status_code}")
                print(f"📄 Response: {data.get('response', 'No response')[:200]}...")
                print(f"🔍 Pattern matched: {data.get('pattern_matched', 'None')}")
                print(f"📚 Documents found: {data.get('documents_found', 0)}")
            else:
                print(f"❌ Status: {response.status_code}")
                print(f"Error: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
    
    # Test streaming endpoint
    print(f"\n🌊 Testing Streaming Endpoint")
    print("-" * 40)
    
    try:
        response = requests.post(
            f"{base_url}/api/chat/local/stream",
            json={
                "message": "What is pharmacy coverage?",
                "session_token": "test_session_123"
            },
            headers={
                "Content-Type": "application/json",
                "Accept": "text/event-stream"
            },
            stream=True,
            timeout=15
        )
        
        if response.status_code == 200:
            print(f"✅ Streaming Status: {response.status_code}")
            
            # Process streaming response
            chunk_count = 0
            for line in response.iter_lines():
                if line:
                    line_text = line.decode('utf-8')
                    if line_text.startswith('data: '):
                        chunk_count += 1
                        if chunk_count <= 3:  # Only show first few chunks
                            data_part = line_text[6:]  # Remove 'data: '
                            if data_part and data_part != '[DONE]':
                                try:
                                    chunk_data = json.loads(data_part)
                                    print(f"📦 Chunk {chunk_count}: {chunk_data.get('content', '')[:50]}...")
                                except json.JSONDecodeError:
                                    print(f"📦 Chunk {chunk_count}: {data_part[:50]}...")
                        
                        if chunk_count >= 5:  # Stop after a few chunks for testing
                            break
            
            print(f"🔢 Total chunks received: {chunk_count}")
        else:
            print(f"❌ Streaming Status: {response.status_code}")
            print(f"Error: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Streaming request failed: {e}")

if __name__ == "__main__":
    print("🚀 Starting Local Search Test")
    print("Make sure your server is running on http://localhost:5000")
    print()
    
    test_local_search()
    
    print("\n" + "=" * 50)
    print("✅ Local Search Test Complete!")