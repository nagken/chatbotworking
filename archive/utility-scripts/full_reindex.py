#!/usr/bin/env python3
"""
Full re-index of all documents to fix the text extraction issue
"""

import os
import sys
import logging
from datetime import datetime

# Add app to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def full_reindex():
    """Re-index ALL documents to fix text extraction"""
    print("🔄 Full Re-indexing of All Documents")
    print("=" * 50)
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    try:
        from app.services.pdf_indexing_service import PDFIndexingService
        
        # Create new service instance
        service = PDFIndexingService()
        
        print(f"📁 Scanning documents folder: {service.documents_folder}")
        
        # Clear the existing index to force complete re-indexing
        print("🗑️ Clearing existing index...")
        service.documents_index = {}
        
        # Scan and index all documents
        print("🔍 Starting full scan and indexing...")
        start_time = datetime.now()
        
        service.scan_documents()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Count documents with text content
        docs_with_text = 0
        docs_without_text = 0
        total_characters = 0
        
        for doc_path, doc_info in service.documents_index.items():
            full_text = doc_info.get('full_text', '')
            if full_text and len(full_text.strip()) > 0:
                docs_with_text += 1
                total_characters += len(full_text)
            else:
                docs_without_text += 1
        
        print(f"\n📊 Re-indexing Complete!")
        print(f"   ⏱️ Duration: {duration:.1f} seconds")
        print(f"   📁 Total documents: {len(service.documents_index)}")
        print(f"   ✅ Documents with text: {docs_with_text}")
        print(f"   ❌ Documents without text: {docs_without_text}")
        print(f"   📝 Total characters extracted: {total_characters:,}")
        print(f"   📈 Success rate: {(docs_with_text / len(service.documents_index)) * 100:.1f}%")
        
        # Test search for contraceptive coverage
        print(f"\n🔍 Testing search for 'contraceptive coverage'...")
        results = service.search_documents("contraceptive coverage", limit=3)
        
        for i, result in enumerate(results, 1):
            print(f"   {i}. {result['filename']}")
            print(f"      Score: {result['relevance_score']:.1f}")
            print(f"      Snippet: {result.get('snippet', 'No snippet')[:100]}...")
        
    except Exception as e:
        print(f"❌ Error during full re-indexing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    full_reindex()