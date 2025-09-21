#!/usr/bin/env python3
"""
Test the chat system with contraceptive coverage question after re-indexing
"""

import asyncio
import aiohttp
import json

async def test_chat_with_documents():
    """Test chat system with contraceptive coverage question"""
    print("💬 Testing Chat System with Document Content")
    print("=" * 50)
    
    url = "http://127.0.0.1:5000/chat/stream"
    
    payload = {
        "message": "What is contraceptive coverage and how does it work?",
        "conversation_id": "test_contraceptive_123"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            print(f"📤 Sending request: {payload['message']}")
            
            async with session.post(url, json=payload) as response:
                print(f"📊 Response status: {response.status}")
                
                if response.status == 200:
                    print(f"📥 Streaming response:")
                    print("-" * 40)
                    
                    full_response = ""
                    document_links = []
                    
                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        if line.startswith('data: '):
                            try:
                                data = json.loads(line[6:])
                                
                                if data.get('type') == 'content':
                                    content = data.get('content', '')
                                    full_response += content
                                    print(content, end='', flush=True)
                                
                                elif data.get('type') == 'documents':
                                    docs = data.get('documents', [])
                                    document_links.extend(docs)
                                
                            except json.JSONDecodeError:
                                continue
                    
                    print(f"\n{'-' * 40}")
                    print(f"📋 Full response length: {len(full_response)} characters")
                    print(f"📄 Documents found: {len(document_links)}")
                    
                    for i, doc in enumerate(document_links, 1):
                        print(f"   {i}. {doc.get('filename', 'Unknown')}")
                        print(f"      Link: {doc.get('link', 'No link')}")
                    
                    # Check if response contains actual document content
                    contraceptive_indicators = [
                        'contraceptive coverage',
                        'no cost',
                        'mandated',
                        'Compass',
                        'member eligibility',
                        'client support'
                    ]
                    
                    found_indicators = []
                    for indicator in contraceptive_indicators:
                        if indicator.lower() in full_response.lower():
                            found_indicators.append(indicator)
                    
                    print(f"\n🎯 Content Analysis:")
                    print(f"   Found {len(found_indicators)} content indicators: {', '.join(found_indicators)}")
                    
                    if found_indicators:
                        print(f"   ✅ Response contains actual document content!")
                    else:
                        print(f"   ❌ Response appears to be generic, not from documents")
                        
                else:
                    error_text = await response.text()
                    print(f"❌ Error response: {error_text}")
                    
    except Exception as e:
        print(f"❌ Error testing chat: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_chat_with_documents())