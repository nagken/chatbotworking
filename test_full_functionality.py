#!/usr/bin/env python3
"""
Comprehensive test script to verify all CVS Pharmacy Knowledge Assist functionality
including PDF text extraction, document search, and chat integration.
"""

import requests
import json
import sys
import time

BASE_URL = "http://localhost:8000"

def test_health_endpoint():
    """Test the health endpoint"""
    print("Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        print(f"Health Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Health Response: {data}")
            return True
        else:
            print(f"Health endpoint failed: {response.text}")
            return False
    except Exception as e:
        print(f"Health endpoint error: {e}")
        return False

def test_document_search():
    """Test document search with enhanced PDF text extraction"""
    print("\nTesting document search...")
    
    # Test various search queries
    test_queries = [
        "prescription",
        "pharmacy",
        "medication",
        "CVS",
        "billing",
        "refill"
    ]
    
    results = {}
    for query in test_queries:
        try:
            print(f"Searching for: {query}")
            response = requests.get(f"{BASE_URL}/api/documents/search", params={"query": query})
            print(f"Search Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Found {len(data)} results for '{query}'")
                
                # Show first few results with snippets
                for i, doc in enumerate(data[:3]):
                    print(f"  {i+1}. {doc['filename']} (score: {doc.get('relevance_score', 'N/A')})")
                    if 'snippet' in doc:
                        snippet = doc['snippet'][:100] + "..." if len(doc['snippet']) > 100 else doc['snippet']
                        print(f"     Snippet: {snippet}")
                
                results[query] = data
            else:
                print(f"Search failed for '{query}': {response.text}")
                results[query] = None
                
        except Exception as e:
            print(f"Search error for '{query}': {e}")
            results[query] = None
            
    return results

def test_chat_with_search_integration():
    """Test chat endpoint with document search integration"""
    print("\nTesting chat with document search integration...")
    
    # Login first (using dev credentials)
    login_data = {
        "username": "dev@cvs.com",
        "password": "dev123"
    }
    
    try:
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
        print(f"Login Status Code: {login_response.status_code}")
        
        if login_response.status_code == 200:
            login_result = login_response.json()
            token = login_result.get("access_token")
            print("Login successful")
            
            # Test chat with pharmacy-related questions
            headers = {"Authorization": f"Bearer {token}"}
            test_messages = [
                "How do I refill my prescription?",
                "What is the automatic refill program?",
                "Tell me about prescription billing",
                "How do I check my medication coverage?"
            ]
            
            for message in test_messages:
                print(f"\nTesting chat message: {message}")
                chat_data = {"message": message}
                
                chat_response = requests.post(f"{BASE_URL}/api/chat", json=chat_data, headers=headers)
                print(f"Chat Status Code: {chat_response.status_code}")
                
                if chat_response.status_code == 200:
                    chat_result = chat_response.json()
                    response_text = chat_result.get("response", "")
                    print(f"Response length: {len(response_text)} characters")
                    
                    # Check if related documents are included
                    if "Related Documents:" in response_text or "related documents" in response_text.lower():
                        print("✓ Document search integration detected in response")
                    else:
                        print("⚠ No document search integration detected")
                        
                    # Show a snippet of the response
                    snippet = response_text[:200] + "..." if len(response_text) > 200 else response_text
                    print(f"Response snippet: {snippet}")
                else:
                    print(f"Chat failed: {chat_response.text}")
        else:
            print(f"Login failed: {login_response.text}")
            return False
            
    except Exception as e:
        print(f"Chat test error: {e}")
        return False
        
    return True

def test_feedback_system():
    """Test the feedback system"""
    print("\nTesting feedback system...")
    
    try:
        feedback_data = {
            "message": "Test message for feedback",
            "response": "Test response from assistant",
            "feedback": "positive",
            "comment": "This is a test feedback comment"
        }
        
        response = requests.post(f"{BASE_URL}/api/feedback", json=feedback_data)
        print(f"Feedback Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Feedback Response: {result}")
            return True
        else:
            print(f"Feedback failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"Feedback test error: {e}")
        return False

def main():
    """Run all tests"""
    print("=== CVS Pharmacy Knowledge Assist Functionality Test ===\n")
    
    # Wait a moment for server to be ready
    print("Waiting for server to be ready...")
    time.sleep(2)
    
    all_passed = True
    
    # Test health endpoint
    if not test_health_endpoint():
        all_passed = False
    
    # Test document search
    search_results = test_document_search()
    if not any(search_results.values()):
        print("⚠ No search results found - this might indicate PDF indexing issues")
        all_passed = False
    else:
        print("✓ Document search is working")
    
    # Test chat integration
    if not test_chat_with_search_integration():
        all_passed = False
    
    # Test feedback system
    if not test_feedback_system():
        all_passed = False
    
    print(f"\n=== Test Summary ===")
    if all_passed:
        print("✓ All tests passed! CVS Pharmacy Knowledge Assist is fully functional.")
    else:
        print("⚠ Some tests failed. Check the output above for details.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
