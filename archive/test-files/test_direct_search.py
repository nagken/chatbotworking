#!/usr/bin/env python3
"""
Direct API test for document search functionality
"""

import requests
import json

def test_document_search_direct():
    """Test document search API directly"""
    
    print("🔐 Step 1: Login...")
    
    # Login
    login_response = requests.post(
        "http://localhost:5000/api/auth/login", 
        json={
            "email": "admin@cvs-pharmacy-knowledge-assist.com",
            "password": "admin123"
        }
    )
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        print(f"Response: {login_response.text}")
        return
    
    login_data = login_response.json()
    token = login_data.get("access_token")
    print(f"✅ Login successful! Token: {token[:20]}...")
    
    print("\n🔍 Step 2: Testing document search...")
    
    # Test high-confidence search queries
    test_queries = [
        "contraceptive coverage",
        "automatic refill",
        "SilverScript",
        "prescription labels",
        "Medicare"
    ]
    
    headers = {"Authorization": f"Bearer {token}"}
    
    for query in test_queries:
        print(f"\n📄 Testing query: '{query}'")
        
        try:
            search_response = requests.get(
                "http://localhost:5000/api/documents/search",
                params={"query": query},
                headers=headers
            )
            
            if search_response.status_code == 200:
                response_data = search_response.json()
                results = response_data.get('results', [])
                total_results = response_data.get('total_results', 0)
                
                print(f"✅ Found {total_results} results")
                
                # Show top 2 results
                for i, doc in enumerate(results[:2], 1):
                    filename = doc.get('filename', 'Unknown')
                    score = doc.get('score', 0)
                    snippet = doc.get('snippet', 'No snippet')[:80]
                    
                    print(f"   {i}. 📁 {filename}")
                    print(f"      📊 Score: {score:.3f}")
                    print(f"      📝 Snippet: \"{snippet}...\"")
                
                if total_results == 0:
                    print("   ⚠️ No results found for this query")
                    
            else:
                print(f"❌ Search failed: {search_response.status_code}")
                print(f"Response: {search_response.text}")
                
        except Exception as e:
            print(f"❌ Error testing '{query}': {e}")
    
    print("\n" + "=" * 60)
    print("🎯 DOCUMENT SEARCH TEST COMPLETE!")

if __name__ == "__main__":
    test_document_search_direct()
