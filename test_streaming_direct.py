#!/usr/bin/env python3
"""
Simple streaming test script to diagnose the chat streaming issues
"""

import asyncio
import aiohttp
import json

async def test_streaming_endpoint():
    """Test the streaming chat endpoint directly"""
    
    print("🧪 Testing CVS Pharmacy Knowledge Assist Streaming")
    print("=" * 50)
    
    url = "http://localhost:5000/api/chat/stream"
    
    test_messages = [
        "How do I process a prescription refill for a member?",
        "What is the Medicare Part D prior authorization process?",
        "How do I help a member with automatic refill enrollment?"
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n🔍 Test {i}: {message}")
        print("-" * 40)
        
        payload = {
            "message": message,
            "conversation_id": None
        }
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
            "Authorization": "Bearer test-token"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    print(f"📊 Status: {response.status}")
                    
                    if response.status != 200:
                        text = await response.text()
                        print(f"❌ Error: {text}")
                        continue
                    
                    print("🌊 Reading streaming response...")
                    message_count = 0
                    full_response = ""
                    
                    async for line in response.content:
                        line_str = line.decode('utf-8').strip()
                        
                        if line_str.startswith('data: '):
                            try:
                                data = json.loads(line_str[6:])  # Remove 'data: '
                                message_count += 1
                                
                                print(f"  📦 Message {message_count}: {data.get('type', 'unknown')}")
                                
                                if data.get('type') == 'system_message':
                                    message_type = data.get('message_type', 'unknown')
                                    print(f"     Message Type: {message_type}")
                                    
                                    if message_type == 'text_response':
                                        content = data.get('data', {}).get('content', '')
                                        is_final = data.get('data', {}).get('is_final', False)
                                        
                                        if content:
                                            full_response = content
                                            print(f"     Content Length: {len(content)} chars")
                                            
                                        if is_final:
                                            print(f"     ✅ Final message received!")
                                            print(f"\n📝 Complete Response:")
                                            print(f"{'='*40}")
                                            print(full_response)
                                            print(f"{'='*40}")
                                            break
                                            
                            except json.JSONDecodeError as e:
                                print(f"     ❌ JSON Parse Error: {e}")
                                print(f"     Raw line: {line_str}")
                    
                    print(f"✅ Test {i} completed. Total messages: {message_count}")
                    
        except Exception as e:
            print(f"❌ Test {i} failed: {e}")
        
        print()
    
    print("🎉 All streaming tests completed!")

if __name__ == "__main__":
    asyncio.run(test_streaming_endpoint())
