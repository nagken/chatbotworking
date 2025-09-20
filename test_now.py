#!/usr/bin/env python3
"""
Test the CVS Pharmacy Knowledge Assist server and PDF search functionality
Run this script after starting the server
"""

import requests
import json
import time
from pathlib import Path

def test_server_and_pdf():
    """Test server health, document search, and chat with PDF integration"""
    
    print("🏥 CVS Pharmacy Knowledge Assist - Test Suite")
    print("=" * 60)
    
    # Test different ports
    ports_to_try = [5000, 8000, 3000, 8080]
    server_port = None
    
    print("\n🔍 Finding server...")
    for port in ports_to_try:
        try:
            response = requests.get(f"http://localhost:{port}/api/health", timeout=3)
            if response.status_code == 200:
                print(f"✅ Server found on port {port}")
                server_port = port
                break
        except:
            continue
    
    if not server_port:
        print("❌ Server not found on any common port")
        print("Please start the server first:")
        print('   python -m uvicorn app.main:app --host 127.0.0.1 --port 5000')
        return
    
    base_url = f"http://localhost:{server_port}"
    
    # Test 1: Health Check
    print(f"\n🏥 Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/api/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return
    
    # Test 2: Document Search API
    print(f"\n📚 Testing document search API...")
    try:
        search_url = f"{base_url}/api/documents/search"
        params = {"query": "contraceptive coverage"}
        
        response = requests.get(search_url, params=params, timeout=10)
        
        if response.status_code == 200:
            results = response.json()
            print(f"✅ Document search successful - Found {len(results)} results")
            
            if results:
                print("\nTop 3 results:")
                for i, doc in enumerate(results[:3], 1):
                    filename = doc.get('filename', 'Unknown')
                    score = doc.get('relevance_score', 'N/A')
                    snippet = doc.get('snippet', 'No snippet')[:80]
                    print(f"   {i}. {filename}")
                    print(f"      Score: {score}")
                    print(f"      Snippet: {snippet}...")
                    print()
            else:
                print("⚠️  No documents found for 'contraceptive coverage'")
                
        else:
            print(f"❌ Document search failed: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Document search error: {e}")
    
    # Test 3: Chat API (should now include document results)
    print(f"\n💬 Testing chat API with PDF integration...")
    try:
        chat_url = f"{base_url}/api/chat"
        payload = {
            "message": "What is contraceptive coverage?",
            "conversation_id": f"test_{int(time.time())}"
        }
        
        response = requests.post(chat_url, json=payload, timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            response_text = result.get('assistant_response', '')
            
            print("✅ Chat API successful")
            print(f"Response length: {len(response_text)} characters")
            
            # Check for document integration
            if 'Related Documents Found' in response_text:
                print("🎉 SUCCESS: Chat response includes PDF search results!")
                print("\nDocument section found in response:")
                # Extract and show the document section
                doc_section_start = response_text.find('📚 **Related Documents Found:**')
                if doc_section_start >= 0:
                    doc_section = response_text[doc_section_start:doc_section_start+500]
                    print(f"   {doc_section[:300]}...")
            else:
                print("⚠️  WARNING: Chat response does NOT include PDF search results")
                print(f"\nResponse preview:\n   {response_text[:200]}...")
                
        else:
            print(f"❌ Chat API failed: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Chat API error: {e}")
    
    # Test 4: Check document resources
    print(f"\n📁 Checking document resources...")
    
    # Check document index
    index_path = Path("document_index.json")
    if index_path.exists():
        try:
            with open(index_path, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
            print(f"✅ Document index: {len(index_data)} documents indexed")
            
            # Check for contraceptive documents specifically
            contraceptive_docs = [k for k in index_data.keys() if 'contraceptive' in k.lower()]
            if contraceptive_docs:
                print(f"   Found {len(contraceptive_docs)} contraceptive-related documents:")
                for doc in contraceptive_docs[:3]:
                    print(f"      - {doc}")
            
        except Exception as e:
            print(f"❌ Error reading document index: {e}")
    else:
        print("❌ Document index not found")
    
    # Check GyaniNuxeo folder
    gyani_path = Path("GyaniNuxeo")
    if gyani_path.exists():
        files = list(gyani_path.glob("*"))
        print(f"✅ GyaniNuxeo folder: {len(files)} files")
    else:
        print("❌ GyaniNuxeo folder not found")
    
    print("\n" + "=" * 60)
    print("🏁 Test complete!")
    print("\nIf PDF search is not working:")
    print("1. Make sure the server is running with the latest code")
    print("2. Check that document_index.json exists and has content")
    print("3. Verify GyaniNuxeo folder has documents")
    print("4. The fixes should now make PDF results appear in chat responses")

if __name__ == "__main__":
    test_server_and_pdf()
