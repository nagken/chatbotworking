#!/usr/bin/env python3

import requests
import json

# Test document endpoint
url = "http://127.0.0.1:5000/api/documents/download/106-29750e_RxCard_DM080718.pdf"

try:
    response = requests.get(url)
    print(f"Status: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    if response.status_code != 200:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Connection error: {e}")

# Also test basic health check
try:
    health = requests.get("http://127.0.0.1:5000/")
    print(f"Health check: {health.status_code}")
except Exception as e:
    print(f"Health check failed: {e}")