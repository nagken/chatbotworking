#!/usr/bin/env python3
"""
Test the enhanced PDF indexing by making API calls to the running server
"""

import requests
import json

def test_enhanced_search():
    """Test enhanced document search via API"""
    base_url = "http://localhost:8080"
    
    # Test queries that should find relevant content
    test_queries = [
        "prior authorization",
        "Medicare Part D",
        "prescription formulary", 
        "member enrollment",
        "copay assistance"
    ]
    
    print("🧪 Testing Enhanced Document Search API")
    print("=" * 50)
    
    for query in test_queries:
        print(f"\n🔍 Searching for: '{query}'")
        
        try:
            # Make API request
            response = requests.get(
                f"{base_url}/api/documents/search",
                params={"query": query, "limit": 3},
                timeout=10
            )
            
            if response.status_code == 200:
                results = response.json()
                print(f"   ✅ Found {len(results)} documents")
                
                for i, doc in enumerate(results, 1):
                    title = doc.get('title', 'Unknown')
                    score = doc.get('relevance_score', 0)
                    snippet = doc.get('snippet', 'No snippet')
                    
                    print(f"   {i}. {title}")
                    print(f"      Score: {score:.1f}")
                    print(f"      Snippet: {snippet[:100]}...")
                    
            else:
                print(f"   ❌ API Error: {response.status_code}")
                print(f"      Response: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Connection Error: {e}")
    
    # Test health endpoint
    print(f"\n🏥 Testing Health Endpoint")
    try:
        response = requests.get(f"{base_url}/api/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print(f"   ✅ Server is healthy")
            print(f"   Status: {health_data.get('status')}")
            print(f"   Timestamp: {health_data.get('timestamp')}")
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Health check error: {e}")

if __name__ == "__main__":
    test_enhanced_search()
