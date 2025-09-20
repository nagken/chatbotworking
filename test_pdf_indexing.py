#!/usr/bin/env python3
"""
Test script for PDF indexing service
"""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app.services.pdf_indexing_service import PDFIndexingService
    
    print("✅ PDF indexing service imported successfully")
    
    # Initialize the service
    service = PDFIndexingService()
    print("✅ PDF indexing service created")
    
    # Test initialization
    success = service.initialize()
    print(f"✅ Initialization {'successful' if success else 'failed'}")
    
    # Get stats
    stats = service.get_stats()
    print(f"📊 Total documents indexed: {stats['total_documents']}")
    print(f"📂 Categories: {list(stats['categories'].keys())}")
    
    # Test search
    if stats['total_documents'] > 0:
        test_query = "prescription medication"
        results = service.search_documents(test_query, limit=3)
        print(f"🔍 Search results for '{test_query}': {len(results)} documents")
        
        for i, result in enumerate(results, 1):
            print(f"{i}. {result.get('title', 'Unknown')} (score: {result.get('relevance_score', 0):.1f})")
            snippet = result.get('snippet', '')
            if snippet:
                print(f"   Snippet: {snippet[:100]}...")
    
    print("✅ PDF indexing test completed successfully")
    
except Exception as e:
    print(f"❌ Error testing PDF indexing: {e}")
    import traceback
    traceback.print_exc()
