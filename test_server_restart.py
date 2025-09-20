#!/usr/bin/env python3
"""
Quick test to verify enhanced PDF indexing is working after server restart
"""

import requests
import time
import json

def test_server_after_restart():
    """Test the enhanced server after restart"""
    base_url = "http://localhost:8080"
    
    print("🔄 Testing Enhanced CVS Pharmacy Knowledge Assist Server")
    print("=" * 60)
    
    # Wait for server to start
    print("⏳ Waiting for server to start...")
    time.sleep(3)
    
    # Test health endpoint
    print("\n🏥 Testing Health Endpoint...")
    try:
        response = requests.get(f"{base_url}/api/health", timeout=10)
        if response.status_code == 200:
            print("   ✅ Health endpoint working")
            health_data = response.json()
            print(f"   Status: {health_data.get('status')}")
            print(f"   Application: {health_data.get('application')}")
        else:
            print(f"   ❌ Health endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Health endpoint error: {e}")
        return False
    
    # Test document search with enhanced features
    print("\n🔍 Testing Enhanced Document Search...")
    
    test_queries = [
        "prior authorization",
        "Medicare Part D", 
        "prescription formulary"
    ]
    
    for query in test_queries:
        print(f"\n   🔍 Searching: '{query}'")
        try:
            response = requests.get(
                f"{base_url}/api/documents/search",
                params={"query": query, "limit": 3},
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                print(f"      ✅ Found {len(results)} documents")
                
                # Check for enhanced features
                has_snippets = False
                has_scores = False
                
                for doc in results:
                    if doc.get('snippet'):
                        has_snippets = True
                    if doc.get('relevance_score', 0) > 0:
                        has_scores = True
                    
                    title = doc.get('title', 'Unknown')[:50]
                    score = doc.get('relevance_score', 0)
                    snippet = doc.get('snippet', '')[:80]
                    
                    print(f"      📄 {title}... (score: {score:.1f})")
                    if snippet:
                        print(f"         💬 {snippet}...")
                
                if has_snippets and has_scores:
                    print(f"      🎯 Enhanced features working! (snippets + scoring)")
                else:
                    print(f"      ⚠️  Basic search only (no enhanced features)")
                    
            elif response.status_code == 422:
                print(f"      ❌ Still getting 422 error - server needs restart")
                return False
            else:
                print(f"      ❌ Search failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"      ❌ Search error: {e}")
            return False
    
    print("\n✅ Enhanced server test completed successfully!")
    print("\n🎯 Try these URLs in your browser:")
    print(f"   Main App: {base_url}")
    print(f"   Health: {base_url}/api/health")
    print(f"   Search: {base_url}/api/documents/search?query=prior%20authorization")
    
    return True

if __name__ == "__main__":
    test_server_after_restart()
