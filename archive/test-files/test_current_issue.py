#!/usr/bin/env python3
"""
Test script to diagnose the PDF search issue in chat responses
"""

import asyncio
import sys
import os
import subprocess
import time
import requests
from pathlib import Path

# Add the app directory to sys.path
sys.path.insert(0, str(Path(__file__).parent))

def check_server_status():
    """Check if server is running on port 5000"""
    try:
        response = requests.get("http://localhost:5000/api/health", timeout=5)
        if response.status_code == 200:
            print("✓ Server is running on port 5000")
            return True
    except:
        pass
    
    try:
        response = requests.get("http://localhost:8000/api/health", timeout=5)
        if response.status_code == 200:
            print("✓ Server is running on port 8000")
            return True
    except:
        pass
    
    print("✗ Server is not running on port 5000 or 8000")
    return False

def test_document_search_api():
    """Test the document search API directly"""
    ports = [5000, 8000]
    
    for port in ports:
        try:
            url = f"http://localhost:{port}/api/documents/search"
            params = {"query": "contraceptive coverage"}
            
            print(f"\nTesting document search API on port {port}...")
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                results = response.json()
                print(f"✓ Document search API working on port {port}")
                print(f"Found {len(results)} results")
                
                if results:
                    for i, result in enumerate(results[:3]):  # Show first 3 results
                        print(f"  Result {i+1}: {result.get('filename')} (score: {result.get('relevance_score', 'N/A')})")
                        snippet = result.get('snippet', '')
                        if snippet:
                            print(f"    Snippet: {snippet[:100]}...")
                else:
                    print("  No results found")
                
                return port, results
            else:
                print(f"✗ Document search API failed on port {port}: {response.status_code}")
                print(f"Response: {response.text[:200]}...")
                
        except Exception as e:
            print(f"✗ Error testing document search on port {port}: {e}")
    
    return None, []

def test_chat_api():
    """Test the chat API to see if it includes document search"""
    ports = [5000, 8000]
    
    for port in ports:
        try:
            url = f"http://localhost:{port}/api/chat"
            payload = {
                "message": "What is contraceptive coverage?",
                "conversation_id": "test_123"
            }
            
            print(f"\nTesting chat API on port {port}...")
            response = requests.post(url, json=payload, timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✓ Chat API working on port {port}")
                
                # Check if response contains document information
                response_text = result.get('response', '')
                if 'Related Documents' in response_text or 'document' in response_text.lower():
                    print("✓ Chat response appears to include document search results")
                else:
                    print("✗ Chat response does not include document search results")
                    print(f"Response preview: {response_text[:200]}...")
                
                return port, result
            else:
                print(f"✗ Chat API failed on port {port}: {response.status_code}")
                print(f"Response: {response.text[:200]}...")
                
        except Exception as e:
            print(f"✗ Error testing chat API on port {port}: {e}")
    
    return None, {}

def check_document_index():
    """Check if the document index exists and has content"""
    index_path = Path("document_index.json")
    
    if index_path.exists():
        try:
            import json
            with open(index_path, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
            
            doc_count = len(index_data)
            print(f"✓ Document index exists with {doc_count} documents")
            
            # Show a few sample documents
            if doc_count > 0:
                print("Sample documents in index:")
                for i, (filename, data) in enumerate(list(index_data.items())[:3]):
                    content_length = len(data.get('content', ''))
                    print(f"  {i+1}. {filename} ({content_length} characters)")
            
            return doc_count
        except Exception as e:
            print(f"✗ Error reading document index: {e}")
            return 0
    else:
        print("✗ Document index file not found")
        return 0

def check_gyani_folder():
    """Check the GyaniNuxeo folder for documents"""
    folder_path = Path("GyaniNuxeo")
    
    if folder_path.exists():
        files = list(folder_path.glob("*"))
        pdf_files = list(folder_path.glob("*.pdf"))
        doc_files = list(folder_path.glob("*.doc*"))
        txt_files = list(folder_path.glob("*.txt"))
        
        print(f"✓ GyaniNuxeo folder exists with {len(files)} total files")
        print(f"  - PDF files: {len(pdf_files)}")
        print(f"  - DOC files: {len(doc_files)}")
        print(f"  - TXT files: {len(txt_files)}")
        
        # Show a few sample files
        print("Sample files:")
        for i, file in enumerate(files[:5]):
            print(f"  {i+1}. {file.name}")
        
        return len(files)
    else:
        print("✗ GyaniNuxeo folder not found")
        return 0

def main():
    """Main test function"""
    print("CVS Pharmacy Knowledge Assist - Diagnostic Test")
    print("=" * 50)
    
    # Check server status
    server_running = check_server_status()
    
    # Check document resources
    print("\nChecking document resources...")
    index_count = check_document_index()
    folder_count = check_gyani_folder()
    
    if not server_running:
        print("\n⚠️  Server is not running. Please start the server first:")
        print("   start_localhost_only.bat")
        print("   or")
        print('   "C:/Program Files/Python/311/python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 5000')
        return
    
    if index_count == 0:
        print("\n⚠️  Document index is empty. PDF search will not work.")
        print("   Consider running the PDF indexing service.")
        return
    
    if folder_count == 0:
        print("\n⚠️  GyaniNuxeo folder is empty. No documents to search.")
        return
    
    # Test APIs
    print("\nTesting APIs...")
    
    # Test document search API
    search_port, search_results = test_document_search_api()
    
    # Test chat API
    chat_port, chat_result = test_chat_api()
    
    # Summary
    print("\n" + "=" * 50)
    print("DIAGNOSTIC SUMMARY:")
    print(f"- Server running: {'Yes' if server_running else 'No'}")
    print(f"- Document index: {index_count} documents")
    print(f"- Document folder: {folder_count} files")
    print(f"- Document search API: {'Working' if search_results else 'Failed'}")
    print(f"- Chat API: {'Working' if chat_result else 'Failed'}")
    
    if search_results and not ('Related Documents' in chat_result.get('response', '')):
        print("\n🔍 ISSUE IDENTIFIED:")
        print("Document search API works, but chat API doesn't include document results.")
        print("This suggests an integration issue in the chat endpoint.")

if __name__ == "__main__":
    main()
