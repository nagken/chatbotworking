#!/usr/bin/env python3
"""
Quick test to check server status and PDF functionality
"""

import requests
import json
import sys
from pathlib import Path

def test_server_ports():
    """Test common ports to find the running server"""
    ports = [5000, 8000, 3000, 8080]
    
    for port in ports:
        try:
            url = f"http://localhost:{port}/api/health"
            response = requests.get(url, timeout=3)
            if response.status_code == 200:
                print(f"✅ Server found on port {port}")
                return port
        except:
            pass
    
    print("❌ No server found on common ports")
    return None

def test_document_search(port):
    """Test document search API"""
    try:
        url = f"http://localhost:{port}/api/documents/search"
        params = {"query": "contraceptive coverage"}
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            results = response.json()
            print(f"✅ Document search API works - Found {len(results)} results")
            
            if results:
                for i, result in enumerate(results[:2], 1):
                    filename = result.get('filename', 'Unknown')
                    score = result.get('score', 0)
                    print(f"   {i}. {filename} (score: {score:.3f})")
            return True
        else:
            print(f"❌ Document search failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Document search error: {e}")
        return False

def test_chat_api(port):
    """Test chat API to see if it includes documents"""
    try:
        url = f"http://localhost:{port}/api/chat"
        payload = {
            "message": "contraceptive coverage",
            "conversation_id": "test123"
        }
        
        response = requests.post(url, json=payload, timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            response_text = result.get('assistant_response', '')
            
            print(f"✅ Chat API works")
            
            # Check if response includes document references
            if 'Related Documents' in response_text:
                print("✅ Chat response includes document search results")
                return True
            else:
                print("❌ Chat response does NOT include document search results")
                print(f"Response preview: {response_text[:200]}...")
                return False
        else:
            print(f"❌ Chat API failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Chat API error: {e}")
        return False

def check_document_resources():
    """Check if document index and folder exist"""
    # Check document index
    index_path = Path("document_index.json")
    if index_path.exists():
        try:
            with open(index_path, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
            print(f"✅ Document index: {len(index_data)} documents")
            index_ok = len(index_data) > 0
        except:
            print("❌ Document index: Error reading file")
            index_ok = False
    else:
        print("❌ Document index: File not found")
        index_ok = False
    
    # Check GyaniNuxeo folder
    folder_path = Path("GyaniNuxeo")
    if folder_path.exists():
        files = list(folder_path.glob("*"))
        print(f"✅ GyaniNuxeo folder: {len(files)} files")
        folder_ok = len(files) > 0
    else:
        print("❌ GyaniNuxeo folder: Not found")
        folder_ok = False
    
    return index_ok and folder_ok

def main():
    print("CVS Pharmacy Knowledge Assist - Quick Status Check")
    print("=" * 60)
    
    # Check document resources
    print("\n📁 Checking document resources...")
    resources_ok = check_document_resources()
    
    # Find server
    print("\n🔍 Looking for running server...")
    port = test_server_ports()
    
    if not port:
        print("\n⚠️  Server is not running. Start the server with:")
        print("   start_localhost_only.bat")
        return
    
    if not resources_ok:
        print("\n⚠️  Document resources missing. PDF search won't work.")
        return
    
    # Test APIs
    print(f"\n🧪 Testing APIs on port {port}...")
    search_ok = test_document_search(port)
    chat_ok = test_chat_api(port)
    
    # Summary
    print("\n" + "=" * 60)
    print("DIAGNOSIS:")
    print(f"Server running: ✅ (port {port})")
    print(f"Document resources: {'✅' if resources_ok else '❌'}")
    print(f"Document search API: {'✅' if search_ok else '❌'}")
    print(f"Chat includes documents: {'✅' if chat_ok else '❌'}")
    
    if search_ok and not chat_ok:
        print("\n🔍 ISSUE FOUND:")
        print("Document search API works, but chat doesn't include results.")
        print("This suggests an integration issue in the chat endpoint.")
    elif not search_ok:
        print("\n🔍 ISSUE FOUND:")
        print("Document search API is not working.")
        print("Check PDF indexing service and document index.")

if __name__ == "__main__":
    main()

# Write results to a file for reference
with open("quick_status_results.txt", "w") as f:
    import sys
    original_stdout = sys.stdout
    sys.stdout = f
    try:
        main()
    finally:
        sys.stdout = original_stdout

print("Results also written to quick_status_results.txt")
