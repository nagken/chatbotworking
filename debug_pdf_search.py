#!/usr/bin/env python3
"""
Direct test of PDF search service to debug the issue
"""

import sys
from pathlib import Path

# Add the app directory to sys.path
sys.path.insert(0, str(Path(__file__).parent))

def test_pdf_search_debug():
    """Test PDF search service directly"""
    try:
        from app.services.pdf_indexing_service import get_pdf_indexing_service
        
        print("Testing PDF search service directly...")
        
        # Get the service
        pdf_service = get_pdf_indexing_service()
        
        # Test with the exact query from the chat
        query = "What is contraceptive coverage?"
        print(f"Query: '{query}'")
        
        # Search documents
        results = pdf_service.search_documents(query, limit=3)
        
        print(f"Results returned: {len(results)}")
        
        if results:
            print("\nSearch results:")
            for i, result in enumerate(results, 1):
                print(f"\n{i}. Filename: {result.get('filename', 'Unknown')}")
                print(f"   Relevance Score: {result.get('relevance_score', 'N/A')}")
                print(f"   Snippet: {result.get('snippet', 'No snippet')[:100]}...")
                print(f"   File Path: {result.get('file_path', 'No path')}")
                
                # Check the score threshold
                score = result.get('relevance_score', 0)
                print(f"   Score > 0.3? {score > 0.3}")
                
        else:
            print("No results found!")
            
        # Test the exact logic from the chat function
        message_lower = query.lower()
        print(f"\nMessage lower: '{message_lower}'")
        print(f"Contains 'contraceptive': {'contraceptive' in message_lower}")
        print(f"Contains 'coverage': {'coverage' in message_lower}")
        
        if results and len(results) > 0:
            top_score = results[0].get('relevance_score', 0)
            print(f"Top result score: {top_score}")
            print(f"Score > 0.3: {top_score > 0.3}")
            
            if top_score > 0.3:
                print("✅ Should trigger document-based response!")
            else:
                print("❌ Score too low, will use generic response")
        else:
            print("❌ No results, will use generic response")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pdf_search_debug()
