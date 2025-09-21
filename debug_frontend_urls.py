#!/usr/bin/env python3

import requests
import urllib.parse

# Test the exact URLs that would be generated in the frontend
test_cases = [
    # Test what the frontend generates vs what works
    {
        'name': 'Frontend URL (encoded)',
        'url': 'http://127.0.0.1:5000/api/documents/download/CLIENT%20SUPPORT-%20MEMBER%20SERVICES%20St%20Joseph%27s%20Women%27s%20Contraceptive%20Coverage'
    },
    {
        'name': 'Direct filename',
        'url': 'http://127.0.0.1:5000/api/documents/download/CLIENT SUPPORT- MEMBER SERVICES St Joseph\'s Women\'s Contraceptive Coverage'
    },
    {
        'name': 'Actual filename from index',
        'url': 'http://127.0.0.1:5000/api/documents/download/_CLIENT SUPPORT- MEMBER SERVICES St Joseph\'s Women\'s Contraceptive Coverage.docx'
    }
]

print("🔍 TESTING DOCUMENT LINK SCENARIOS:")
print("=" * 60)

for test in test_cases:
    print(f"\n📋 {test['name']}:")
    print(f"URL: {test['url']}")
    
    try:
        response = requests.get(test['url'], timeout=10)
        if response.status_code == 200:
            print("✅ SUCCESS - Document downloaded")
            print(f"   Size: {len(response.content)} bytes")
        else:
            print(f"❌ FAILED - Status: {response.status_code}")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ CONNECTION ERROR: {e}")

print(f"\n{'='*60}")
print("💡 TIP: If any test fails, the frontend might be generating wrong URLs")