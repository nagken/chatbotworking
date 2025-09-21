#!/usr/bin/env python3

import requests
import urllib.parse

# Test with exact filename including space
url = "http://127.0.0.1:5000/api/documents/download/106-29750e_RxCard_DM080718 .pdf"

print(f"Testing: {url}")

try:
    response = requests.get(url)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ DOCUMENT DOWNLOAD WORKS!")
        print(f"Content-Type: {response.headers.get('content-type')}")
        print(f"Content-Length: {response.headers.get('content-length')}")
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Error: {e}")