#!/usr/bin/env python3
"""
Quick test to verify PDF text extraction is working
"""

import os
import sys
import json

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app.services.pdf_indexing_service import PDFIndexingService
    
    print("✅ Starting enhanced PDF indexing test...")
    
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
    
    # Test search with pharmacy-related queries
    test_queries = [
        "prescription medication",
        "prior authorization", 
        "Medicare Part D",
        "formulary coverage"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Testing search for: '{query}'")
        results = service.search_documents(query, limit=3)
        print(f"   Found {len(results)} documents")
        
        for i, result in enumerate(results, 1):
            title = result.get('title', 'Unknown')
            score = result.get('relevance_score', 0)
            snippet = result.get('snippet', '')
            
            print(f"   {i}. {title} (score: {score:.1f})")
            if snippet:
                print(f"      Snippet: {snippet[:150]}...")
            
    # Test if we're actually extracting text content
    if stats['total_documents'] > 0:
        print(f"\n🔍 Checking if text extraction is working...")
        # Get a sample document to check if it has text content
        sample_doc_path = list(service.documents_index.keys())[0]
        sample_doc = service.documents_index[sample_doc_path]
        
        full_text = sample_doc.get('full_text', '')
        text_content = sample_doc.get('text_content', '')
        
        print(f"   Sample document: {sample_doc.get('filename', 'Unknown')}")
        print(f"   Has full_text: {len(full_text) > 0} ({len(full_text)} chars)")
        print(f"   Has text_content: {len(text_content) > 0} ({len(text_content)} chars)")
        
        if len(full_text) > 100:
            print(f"   Text preview: {full_text[:200]}...")
    
    print("✅ Enhanced PDF indexing test completed successfully")
    
except Exception as e:
    print(f"❌ Error testing PDF indexing: {e}")
    import traceback
    traceback.print_exc()
