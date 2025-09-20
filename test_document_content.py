#!/usr/bin/env python3
"""
Test document content extraction to verify PDF/Word text is being read properly
"""

import os
import sys

# Add app to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def test_document_content():
    """Test actual document content extraction"""
    print("🔍 Testing Document Content Extraction")
    print("=" * 60)
    
    try:
        from app.services.pdf_indexing_service import PDFIndexingService
        
        # Initialize service
        pdf_service = PDFIndexingService()
        pdf_service.load_index()
        
        # Test specific contraceptive documents
        test_files = [
            "GyaniNuxeo\\PD  72703 Compass - Contraceptives_Card NEW as of 12022024.docx",
            "GyaniNuxeo\\_CLIENT SUPPORT- MEMBER SERVICES St Joseph's Women's Contraceptive Coverage.docx",
            "GyaniNuxeo\\PD 80724 Contraceptives_Card pulled 10022024.docx"
        ]
        
        for file_path in test_files:
            print(f"\n📄 Testing: {os.path.basename(file_path)}")
            print("-" * 50)
            
            if os.path.exists(file_path):
                # Get document info from index
                doc_info = pdf_service.get_document_info(file_path)
                
                if doc_info:
                    print(f"✅ Document found in index")
                    print(f"   Title: {doc_info.get('title', 'N/A')}")
                    print(f"   Category: {doc_info.get('category', 'N/A')}")
                    
                    # Check if full text is available
                    full_text = doc_info.get('full_text', '')
                    if full_text:
                        print(f"✅ Full text available: {len(full_text)} characters")
                        
                        # Show first few lines
                        lines = full_text.split('\n')
                        print(f"\n📝 First few lines of content:")
                        for i, line in enumerate(lines[:10], 1):
                            if line.strip():
                                print(f"   {i}. {line.strip()[:100]}...")
                        
                        # Test search for "contraceptive"
                        if 'contraceptive' in full_text.lower():
                            print(f"\n🎯 Contains 'contraceptive': YES")
                            snippet = pdf_service.extract_relevant_snippet(
                                'contraceptive', full_text, snippet_length=300
                            )
                            if snippet:
                                print(f"📋 Relevant snippet: {snippet[:200]}...")
                        else:
                            print(f"\n🎯 Contains 'contraceptive': NO")
                            
                    else:
                        print(f"❌ No full text available")
                        
                        # Try to extract manually
                        print(f"🔧 Attempting manual extraction...")
                        try:
                            file_ext = os.path.splitext(file_path)[1].lower()
                            extracted_text = pdf_service.extract_text_from_file(file_path, file_ext)
                            if extracted_text:
                                print(f"✅ Manual extraction successful: {len(extracted_text)} characters")
                                print(f"📝 Sample content: {extracted_text[:200]}...")
                            else:
                                print(f"❌ Manual extraction failed")
                        except Exception as e:
                            print(f"❌ Manual extraction error: {e}")
                else:
                    print(f"❌ Document not found in index")
            else:
                print(f"❌ File does not exist: {file_path}")
        
        # Test search functionality
        print(f"\n🔍 Testing Search Functionality")
        print("=" * 50)
        
        search_results = pdf_service.search_documents("contraceptive coverage", limit=5)
        print(f"📊 Search results for 'contraceptive coverage': {len(search_results)} documents")
        
        for i, result in enumerate(search_results[:3], 1):
            print(f"\n{i}. {result['title']}")
            print(f"   File: {result['filename']}")
            print(f"   Score: {result['relevance_score']}")
            if 'snippet' in result:
                print(f"   Snippet: {result['snippet'][:150]}...")
            
    except Exception as e:
        print(f"❌ Error testing document content: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_document_content()