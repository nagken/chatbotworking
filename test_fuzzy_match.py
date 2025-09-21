#!/usr/bin/env python3

import requests

# Test both document URLs from the interface
test_docs = [
    "CLIENT SUPPORT- MEMBER SERVICES St Joseph's Women's Contraceptive Coverage",
    "106-29750e RxCard DM080718",
    "_CLIENT SUPPORT- MEMBER SERVICES St Joseph's Women's Contraceptive Coverage.docx",
    "106-29750e_RxCard_DM080718 .pdf"
]

for doc in test_docs:
    url = f"http://127.0.0.1:5000/api/documents/download/{doc}"
    print(f"\nTesting: {doc}")
    
    try:
        response = requests.get(url)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ SUCCESS!")
            content_type = response.headers.get('content-type', 'unknown')
            content_length = response.headers.get('content-length', 'unknown')
            print(f"  Content-Type: {content_type}")
            print(f"  Size: {content_length} bytes")
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Connection error: {e}")