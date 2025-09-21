#!/usr/bin/env python3
"""
Quick test to verify PDF indexing service is working
"""

import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

try:
    from app.services.pdf_indexing_service import get_pdf_indexing_service
    
    print("🔍 Testing PDF indexing service...")
    
    # Get the service
    pdf_service = get_pdf_indexing_service()
    
    # Test search
    query = "contraceptive coverage"
    results = pdf_service.search_documents(query, limit=5)
    
    print(f"📊 Search for '{query}' returned {len(results)} results")
    
    for i, doc in enumerate(results[:3], 1):
        print(f"\n{i}. Document: {doc.get('filename', 'Unknown')}")
        print(f"   Score: {doc.get('score', 0):.3f}")
        print(f"   Snippet: {doc.get('snippet', 'No snippet')[:80]}...")
        print(f"   Path: {doc.get('file_path', 'No path')}")
    
    if len(results) == 0:
        print("❌ No results found! PDF indexing may not be working.")
    else:
        print(f"✅ PDF search is working! Found {len(results)} documents.")
        
except Exception as e:
    print(f"❌ Error testing PDF service: {e}")
    import traceback
    traceback.print_exc()
