#!/usr/bin/env python3
"""
Test text extraction from specific contraceptive documents
"""

import os
import sys
import traceback

# Add app to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def test_text_extraction():
    """Test text extraction from contraceptive documents"""
    print("🔍 Testing Text Extraction from Documents")
    print("=" * 50)
    
    # Test imports first
    try:
        import PyPDF2
        print("✅ PyPDF2 imported successfully")
    except ImportError as e:
        print(f"❌ PyPDF2 import failed: {e}")
        return
    
    try:
        from docx import Document
        print("✅ python-docx imported successfully")
    except ImportError as e:
        print(f"❌ python-docx import failed: {e}")
        return
    
    # Test specific contraceptive files
    test_files = [
        "GyaniNuxeo\\PD  72703 Compass - Contraceptives_Card NEW as of 12022024.docx",
        "GyaniNuxeo\\_CLIENT SUPPORT- MEMBER SERVICES St Joseph's Women's Contraceptive Coverage.docx"
    ]
    
    for file_path in test_files:
        print(f"\n📄 Testing: {os.path.basename(file_path)}")
        
        if not os.path.exists(file_path):
            print(f"   ❌ File not found: {file_path}")
            continue
        
        try:
            # Test DOCX extraction
            if file_path.endswith('.docx'):
                doc = Document(file_path)
                text = ""
                for paragraph in doc.paragraphs:
                    text += paragraph.text + "\n"
                
                text = text.strip()
                if text:
                    print(f"   ✅ Extracted {len(text)} characters")
                    print(f"   📝 Sample: {text[:300]}...")
                    
                    # Check for contraceptive content
                    if 'contraceptive' in text.lower():
                        print(f"   🎯 Contains 'contraceptive': YES")
                    else:
                        print(f"   🎯 Contains 'contraceptive': NO")
                else:
                    print(f"   ❌ No text extracted")
                    
        except Exception as e:
            print(f"   ❌ Error extracting text: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    test_text_extraction()