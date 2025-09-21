#!/usr/bin/env python3

import requests
import json
import time

def test_actual_document_search():
    """Test what documents are actually found when searching for contraceptive coverage"""
    
    # Test document search API directly
    search_url = "http://127.0.0.1:5000/api/documents/search"
    
    session = requests.Session()
    
    # Login first
    login_data = {
        "email": "admin@pss-knowledge-assist.com", 
        "password": "admin123"
    }
    login_response = session.post("http://127.0.0.1:5000/api/auth/login", json=login_data)
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        return
        
    print("✅ Login successful")
    
    # Search for contraceptive documents
    search_params = {"query": "contraceptive coverage", "limit": 10}
    search_response = session.get(search_url, params=search_params)
    
    if search_response.status_code == 200:
        search_results = search_response.json()
        print(f"\n🔍 Document search results for 'contraceptive coverage':")
        print(f"Found {len(search_results.get('documents', []))} documents")
        
        for i, doc in enumerate(search_results.get('documents', [])[:5]):
            print(f"\nDocument {i+1}:")
            print(f"  Filename: {doc.get('filename', 'Unknown')}")
            print(f"  Similarity: {doc.get('similarity', 'Unknown')}")
            print(f"  Content preview: {doc.get('content', 'No content')[:100]}...")
            
            # Test if the document URL works
            filename = doc.get('filename', '')
            if filename:
                doc_url = f"http://127.0.0.1:5000/documents/{filename}"
                try:
                    doc_response = session.head(doc_url, timeout=5)
                    if doc_response.status_code == 200:
                        print(f"  ✅ Document accessible at: {doc_url}")
                    else:
                        print(f"  ❌ Document not accessible: {doc_response.status_code}")
                except Exception as e:
                    print(f"  ❌ Error accessing document: {e}")
    else:
        print(f"❌ Search failed: {search_response.status_code}")
        print(search_response.text)

def test_specific_files():
    """Test if the specific files mentioned by AI actually exist"""
    
    session = requests.Session()
    
    # Login
    login_data = {"email": "admin@pss-knowledge-assist.com", "password": "admin123"}
    session.post("http://127.0.0.1:5000/api/auth/login", json=login_data)
    
    # Files mentioned by AI
    ai_mentioned_files = [
        "106-29750e_RxCard_DM080718.pdf",
        "_CLIENT SUPPORT- MEMBER SERVICES St Joseph's Women's Contraceptive Coverage.docx"
    ]
    
    # Actual files we found in directory
    actual_files = [
        "106-29750e_RxCard_DM080718 .pdf",  # Note the space before .pdf
        "_CLIENT SUPPORT- MEMBER SERVICES St Joseph's Women's Contraceptive Coverage.docx"
    ]
    
    print("\n🔍 Testing document accessibility:")
    
    for filename in ai_mentioned_files + actual_files:
        doc_url = f"http://127.0.0.1:5000/documents/{filename}"
        try:
            response = session.head(doc_url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {filename} - ACCESSIBLE")
            else:
                print(f"❌ {filename} - ERROR {response.status_code}")
        except Exception as e:
            print(f"❌ {filename} - EXCEPTION: {e}")

if __name__ == "__main__":
    test_actual_document_search()
    test_specific_files()