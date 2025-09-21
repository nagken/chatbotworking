#!/usr/bin/env python3

import requests
import urllib.parse

def test_document_routes():
    """Test the document serving routes"""
    
    session = requests.Session()
    
    # Login
    login_data = {"email": "admin@pss-knowledge-assist.com", "password": "admin123"}
    login_response = session.post("http://127.0.0.1:5000/api/auth/login", json=login_data)
    
    if login_response.status_code != 200:
        print("❌ Login failed")
        return
        
    print("✅ Login successful")
    
    # Test actual contraceptive documents found by search
    test_files = [
        "_CLIENT SUPPORT- MEMBER SERVICES St Joseph's Women's Contraceptive Coverage.docx",
        "PD  72703 Compass - Contraceptives_Card NEW as of 12022024.docx",
        "106-29750e_RxCard_DM080718 .pdf"  # Note the space before .pdf
    ]
    
    for filename in test_files:
        print(f"\n🔍 Testing: {filename}")
        
        # URL encode the filename
        encoded_filename = urllib.parse.quote(filename)
        doc_url = f"http://127.0.0.1:5000/documents/{encoded_filename}"
        
        print(f"URL: {doc_url}")
        
        try:
            # Test GET request
            response = session.get(doc_url, timeout=5)
            print(f"GET Status: {response.status_code}")
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', 'unknown')
                content_length = response.headers.get('content-length', 'unknown')
                print(f"✅ SUCCESS - Type: {content_type}, Size: {content_length} bytes")
            else:
                print(f"❌ FAILED - Status: {response.status_code}")
                print(f"   Response: {response.text[:100]}")
                
        except Exception as e:
            print(f"❌ EXCEPTION: {e}")

if __name__ == "__main__":
    test_document_routes()