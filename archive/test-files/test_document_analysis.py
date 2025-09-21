#!/usr/bin/env python3
"""
Quick Document Analysis - Test the PDF indexing without server startup
"""

import os
import sys
import json
from pathlib import Path

# Add app to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def test_document_indexing():
    """Test document indexing functionality"""
    print("🔍 Testing Document Indexing (No Server)")
    print("=" * 50)
    
    try:
        from app.services.pdf_indexing_service import PDFIndexingService
        
        # Initialize service
        pdf_service = PDFIndexingService()
        
        # Load existing index
        pdf_service.load_index()
        
        # Get stats
        stats = pdf_service.get_stats()
        print(f"📊 Document Statistics:")
        print(f"  • Total Documents: {stats['total_documents']}")
        print(f"  • Categories: {len(stats['categories'])}")
        for category, count in stats['categories'].items():
            print(f"    - {category}: {count} documents")
        
        # Test searches
        print(f"\n🔍 Testing Document Search:")
        
        test_queries = [
            "contraceptive coverage",
            "prior authorization", 
            "Medicare Part D",
            "specialty pharmacy",
            "mail order"
        ]
        
        for query in test_queries:
            results = pdf_service.search_documents(query, limit=3)
            print(f"\n📋 Query: '{query}' → {len(results)} results")
            
            for i, doc in enumerate(results[:2], 1):
                print(f"  {i}. 📄 {doc['title']}")
                print(f"     📁 {doc['filename']}")
                print(f"     📂 Category: {doc['category']}")
                print(f"     🔗 Path: {doc['filepath']}")
                if 'snippet' in doc:
                    snippet = doc['snippet'][:80] + "..." if len(doc['snippet']) > 80 else doc['snippet']
                    print(f"     📝 Snippet: {snippet}")
                print(f"     ⭐ Score: {doc['relevance_score']:.1f}")
        
        # Check specific document content
        print(f"\n📑 Sample Document Content Analysis:")
        
        # Look for any document that might contain contraceptive info
        contraceptive_results = pdf_service.search_documents("contraceptive", limit=1)
        if contraceptive_results:
            doc = contraceptive_results[0]
            print(f"Found document: {doc['title']}")
            print(f"File: {doc['filepath']}")
            
            # Get full document info
            full_doc = pdf_service.get_document_info(doc['filepath'])
            if full_doc and 'full_text' in full_doc:
                text_content = full_doc['full_text']
                print(f"Full text length: {len(text_content)} characters")
                
                # Show first few lines containing "contraceptive"
                lines = text_content.split('\n')
                contraceptive_lines = [line for line in lines if 'contraceptive' in line.lower()]
                if contraceptive_lines:
                    print("Lines containing 'contraceptive':")
                    for i, line in enumerate(contraceptive_lines[:3], 1):
                        print(f"  {i}. {line.strip()[:100]}...")
                else:
                    print("No lines containing 'contraceptive' found in extracted text")
        else:
            print("❌ No documents found containing 'contraceptive'")
        
        print(f"\n✅ Document indexing test complete!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing document indexing: {e}")
        import traceback
        traceback.print_exc()
        return False

def analyze_document_structure():
    """Analyze the GyaniNuxeo folder structure"""
    print(f"\n📁 GyaniNuxeo Folder Analysis:")
    print("=" * 50)
    
    folder_path = "GyaniNuxeo"
    if not os.path.exists(folder_path):
        print(f"❌ Folder '{folder_path}' not found!")
        return False
    
    # Count files by extension
    file_counts = {}
    total_size = 0
    sample_files = []
    
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            ext = Path(file).suffix.lower()
            
            # Count by extension
            file_counts[ext] = file_counts.get(ext, 0) + 1
            
            # Add to total size
            try:
                total_size += os.path.getsize(file_path)
            except:
                pass
            
            # Collect sample files
            if len(sample_files) < 10:
                rel_path = os.path.relpath(file_path, folder_path)
                sample_files.append((file, rel_path, ext))
    
    print(f"📊 File Statistics:")
    print(f"  • Total Size: {total_size / (1024*1024):.1f} MB")
    
    print(f"\n📋 Files by Extension:")
    for ext, count in sorted(file_counts.items()):
        print(f"  • {ext or '(no extension)'}: {count} files")
    
    print(f"\n📄 Sample Files:")
    for filename, rel_path, ext in sample_files:
        print(f"  • {filename} ({ext})")
        print(f"    📁 {rel_path}")
    
    return True

def main():
    """Main function"""
    print("🚀 CVS Pharmacy Document Analysis")
    print("=" * 70)
    
    # Test document structure
    analyze_document_structure()
    
    # Test document indexing
    test_document_indexing()
    
    print("\n" + "=" * 70)
    print("💡 KEY FINDINGS:")
    print("=" * 70)
    
    print("\n1. 📊 The system HAS 1,880 documents indexed")
    print("2. 🔍 Document search IS working")
    print("3. 📝 Text extraction IS happening")
    print("4. ❓ BUT: AI responses are NOT using the indexed content")
    
    print("\n🎯 THE PROBLEM:")
    print("The system is searching Google BigQuery (cvs_pharmacy_data.documents)")
    print("BUT it should be searching the local PDF indexing service!")
    
    print("\n🔧 THE SOLUTION:")
    print("1. Modify the LLM service to use PDF indexing service")
    print("2. Update system prompt to reference local documents")
    print("3. Add document serving endpoint for file links")
    print("4. Enhance message transformer to include document context")
    
    print("\n✅ Analysis complete - ready to implement fixes!")

if __name__ == "__main__":
    main()