#!/usr/bin/env python3
"""
Re-index documents with detailed logging to see what's happening
"""

import os
import sys
import logging

# Add app to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def reindex_documents():
    """Re-index documents with debug logging"""
    print("🔄 Re-indexing Documents with Debug Logging")
    print("=" * 50)
    
    # Set up detailed logging
    logging.basicConfig(level=logging.DEBUG)
    
    try:
        from app.services.pdf_indexing_service import PDFIndexingService
        
        # Create new service instance
        service = PDFIndexingService()
        
        # Test indexing a specific contraceptive document
        test_file = "GyaniNuxeo\\PD  72703 Compass - Contraceptives_Card NEW as of 12022024.docx"
        
        if os.path.exists(test_file):
            print(f"\n📄 Re-indexing: {os.path.basename(test_file)}")
            
            # Clear existing entry to force re-indexing
            relative_path = os.path.relpath(test_file)
            if relative_path in service.documents_index:
                del service.documents_index[relative_path]
                print(f"   🗑️ Cleared existing index entry")
            
            # Re-index the document
            service.index_document(test_file)
            
            # Check what was indexed
            if relative_path in service.documents_index:
                doc_info = service.documents_index[relative_path]
                full_text = doc_info.get('full_text', '')
                
                print(f"   📊 Indexed successfully:")
                print(f"      Title: {doc_info.get('title', 'N/A')}")
                print(f"      Category: {doc_info.get('category', 'N/A')}")
                print(f"      Full text length: {len(full_text) if full_text else 0}")
                
                if full_text:
                    print(f"      ✅ Text content: {full_text[:200]}...")
                    
                    # Save the updated index
                    service.save_index()
                    print(f"   💾 Saved updated index")
                else:
                    print(f"      ❌ No text content!")
                    
        else:
            print(f"❌ Test file not found: {test_file}")
            
    except Exception as e:
        print(f"❌ Error during re-indexing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    reindex_documents()