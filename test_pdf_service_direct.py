#!/usr/bin/env python3
"""
Test the PDF indexing service directly
"""

import sys
from pathlib import Path

# Add the app directory to sys.path
sys.path.insert(0, str(Path(__file__).parent))

def test_pdf_service():
    """Test the PDF indexing service"""
    try:
        from app.services.pdf_indexing_service import get_pdf_indexing_service
        
        print("Testing PDF indexing service...")
        
        # Get the service
        pdf_service = get_pdf_indexing_service()
        
        # Test document search
        query = "contraceptive coverage"
        print(f"Searching for: '{query}'")
        
        results = pdf_service.search_documents(query, limit=5)
        
        print(f"Found {len(results)} results:")
        
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result.get('filename', 'Unknown')}")
            print(f"   Score: {result.get('score', 0):.3f}")
            print(f"   Snippet: {result.get('snippet', 'No snippet')[:100]}...")
            
        return len(results) > 0
        
    except Exception as e:
        print(f"Error testing PDF service: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_document_index():
    """Check if document index exists and has content"""
    try:
        import json
        index_path = Path("document_index.json")
        
        if not index_path.exists():
            print("❌ document_index.json not found")
            return False
            
        with open(index_path, 'r', encoding='utf-8') as f:
            index_data = json.load(f)
            
        print(f"✅ Document index loaded with {len(index_data)} documents")
        
        # Show some sample documents
        if index_data:
            print("\nSample documents:")
            for i, (filename, data) in enumerate(list(index_data.items())[:3]):
                content_length = len(data.get('content', ''))
                print(f"  {i+1}. {filename} ({content_length} chars)")
                
        return len(index_data) > 0
        
    except Exception as e:
        print(f"Error reading document index: {e}")
        return False

def test_gyani_folder():
    """Check GyaniNuxeo folder"""
    try:
        folder_path = Path("GyaniNuxeo")
        
        if not folder_path.exists():
            print("❌ GyaniNuxeo folder not found")
            return False
            
        files = list(folder_path.glob("*"))
        print(f"✅ GyaniNuxeo folder contains {len(files)} files")
        
        # Count by type
        doc_files = list(folder_path.glob("*.doc*"))
        pdf_files = list(folder_path.glob("*.pdf"))
        txt_files = list(folder_path.glob("*.txt"))
        
        print(f"   - DOC files: {len(doc_files)}")
        print(f"   - PDF files: {len(pdf_files)}")
        print(f"   - TXT files: {len(txt_files)}")
        
        return len(files) > 0
        
    except Exception as e:
        print(f"Error checking GyaniNuxeo folder: {e}")
        return False

if __name__ == "__main__":
    print("CVS Pharmacy PDF Service Test")
    print("=" * 40)
    
    # Test components
    index_ok = test_document_index()
    folder_ok = test_gyani_folder()
    service_ok = test_pdf_service()
    
    print("\n" + "=" * 40)
    print("SUMMARY:")
    print(f"Document Index: {'✅' if index_ok else '❌'}")
    print(f"Document Folder: {'✅' if folder_ok else '❌'}")
    print(f"PDF Service: {'✅' if service_ok else '❌'}")
    
    if all([index_ok, folder_ok, service_ok]):
        print("\n🎉 PDF search should work when server is running!")
    else:
        print("\n⚠️  Issues found - PDF search may not work properly")
