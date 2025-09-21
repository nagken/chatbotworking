#!/usr/bin/env python3
"""
Simple test for document links functionality
"""

import requests
import json
import time

def test_simple_chat():
    """Simple test without timeout issues"""
    
    print("Waiting for server to be ready...")
    time.sleep(5)  # Give server time to start
    
    print("Testing contraceptive coverage question...")
    
    try:
        url = "http://127.0.0.1:5000/api/chat"
        payload = {
            "message": "What is contraceptive coverage?",
            "conversation_id": "test_simple_123"
        }
        
        response = requests.post(url, json=payload, timeout=30)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            assistant_response = result.get('assistant_response', '')
            
            print(f"Response length: {len(assistant_response)} characters")
            
            # Check for document references
            if '(Document' in assistant_response:
                import re
                doc_refs = re.findall(r'\(Document \d+: ([^)]+)\)', assistant_response)
                print(f"✅ Found {len(doc_refs)} document references:")
                for i, ref in enumerate(doc_refs, 1):
                    print(f"  {i}. {ref}")
            else:
                print("❌ No document references found")
                
            # Show partial response
            print("\nResponse preview:")
            print("-" * 40)
            print(assistant_response[:300])
            print("..." if len(assistant_response) > 300 else "")
            print("-" * 40)
            
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_simple_chat()