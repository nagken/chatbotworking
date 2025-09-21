#!/usr/bin/env python3
"""
Quick test to verify specific CVS documents are indexed and searchable
"""

import requests
import json

def test_specific_documents():
    """Test specific known documents from GyaniNuxeo folder"""
    
    # Login first
    login_data = {
        "email": "admin@cvs-pharmacy-knowledge-assist.com",
        "password": "admin123"
    }
    
    print("🔐 Logging in...")
    login_response = requests.post("http://localhost:5000/api/auth/login", json=login_data)
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        return
    
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test queries with expected documents
    test_cases = [
        {
            "query": "contraceptive coverage",
            "expected_filename": "_CLIENT SUPPORT- MEMBER SERVICES St Joseph's Women's Contraceptive Coverage.docx",
            "description": "Should find contraceptive coverage document"
        },
        {
            "query": "automatic refill program",
            "expected_filename": "001628 MED D - Automatic Refill Program (ARP).docx",
            "description": "Should find ARP document"
        },
        {
            "query": "prescription labels",
            "expected_filename": "011600 Prescription Labels 07.21.25.docx",
            "description": "Should find prescription labels document"
        },
        {
            "query": "Medicare Part D",
            "expected_contains": "MED D",
            "description": "Should find Medicare documents"
        },
        {
            "query": "SilverScript",
            "expected_filename": "002996 MED D - SilverScript and Blue MedicareRx (NEJE) - Enrollment Related RM Tasks 122123.doc",
            "description": "Should find SilverScript document"
        }
    ]
    
    print(f"\n🧪 Testing {len(test_cases)} specific document searches...")
    print("=" * 80)
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: '{test['query']}'")
        print(f"   Expected: {test['description']}")
        
        # Perform search
        response = requests.get(
            f"http://localhost:5000/api/documents/search",
            params={"query": test["query"]},
            headers=headers
        )
        
        if response.status_code == 200:
            results = response.json()
            print(f"   📊 Found {len(results)} results")
            
            # Check if expected document is found
            found_expected = False
            
            for result in results[:5]:  # Check top 5 results
                filename = result.get('filename', '')
                score = result.get('score', 0)
                snippet = result.get('snippet', '')[:100]
                
                # Check for expected filename or content
                if 'expected_filename' in test and test['expected_filename'].lower() in filename.lower():
                    found_expected = True
                    print(f"   ✅ FOUND EXPECTED: {filename} (score: {score:.3f})")
                    print(f"      Snippet: \"{snippet}...\"")
                    break
                elif 'expected_contains' in test and test['expected_contains'].lower() in filename.lower():
                    found_expected = True
                    print(f"   ✅ FOUND MATCHING: {filename} (score: {score:.3f})")
                    print(f"      Snippet: \"{snippet}...\"")
                    break
            
            if not found_expected and results:
                print(f"   ⚠️  Expected document not in top results, but found {len(results)} other results:")
                for result in results[:2]:
                    print(f"      📄 {result.get('filename', 'Unknown')} (score: {result.get('score', 0):.3f})")
            elif not results:
                print(f"   ❌ No results found")
                
        else:
            print(f"   ❌ Search failed: {response.status_code}")
    
    print("\n" + "=" * 80)
    print("🎯 CONFIDENCE TEST COMPLETE!")
    print("\n📋 RECOMMENDED TEST QUERIES FOR MANUAL TESTING:")
    print("1. 'contraceptive coverage' - Should find specific document")
    print("2. 'automatic refill program' - Should find ARP document") 
    print("3. 'prescription labels' - Should find labels document")
    print("4. 'SilverScript' - Should find specific SilverScript document")
    print("5. 'Medicare' - Should find multiple Medicare documents")

if __name__ == "__main__":
    test_specific_documents()
