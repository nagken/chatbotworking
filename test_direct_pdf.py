#!/usr/bin/env python3
"""
Direct test of enhanced PDF indexing without server startup
"""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_pdf_extraction():
    """Test PDF text extraction directly"""
    try:
        from app.services.pdf_indexing_service import PDFIndexingService
        
        print("🧪 Testing enhanced PDF indexing...")
        
        # Initialize service directly
        service = PDFIndexingService("GyaniNuxeo")
        
        # Test text extraction on a few files
        test_files = [
            "GyaniNuxeo/015421 MED D - Appointment of Representative (AOR) form - Large Print.pdf",
            "GyaniNuxeo/015422 MED D - Appointment of Representative (AOR) form - Spanish.pdf",
            "GyaniNuxeo/053118 MED D - OutcomesMTM Sample Prescriber Fax Form.pdf"
        ]
        
        for file_path in test_files:
            if os.path.exists(file_path):
                print(f"\n📄 Testing: {os.path.basename(file_path)}")
                
                try:
                    # Test text extraction
                    extracted_text = service.extract_text_from_pdf(file_path)
                    
                    if extracted_text:
                        print(f"   ✅ Extracted {len(extracted_text)} characters")
                        print(f"   Preview: {extracted_text[:200]}...")
                    else:
                        print(f"   ⚠️  No text extracted")
                        
                except Exception as e:
                    print(f"   ❌ Error extracting from {file_path}: {e}")
            else:
                print(f"   📁 File not found: {file_path}")
        
        # Test initialization and indexing
        print(f"\n🔄 Initializing service and indexing documents...")
        success = service.initialize()
        
        if success:
            stats = service.get_stats()
            print(f"   ✅ Indexed {stats['total_documents']} documents")
            
            # Test search
            query = "prescription"
            results = service.search_documents(query, limit=3)
            print(f"\n🔍 Search results for '{query}': {len(results)} found")
            
            for i, result in enumerate(results, 1):
                title = result.get('title', 'Unknown')
                score = result.get('relevance_score', 0)
                snippet = result.get('snippet', '')
                
                print(f"   {i}. {title} (score: {score:.1f})")
                if snippet:
                    print(f"      📝 {snippet[:100]}...")
        else:
            print(f"   ❌ Service initialization failed")
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pdf_extraction()
