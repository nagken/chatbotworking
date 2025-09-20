#!/usr/bin/env python3
"""
Quick test to check if documents have extracted text content
"""

import os
import sys
import json

# Add app to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def check_document_index():
    """Check if the document index contains actual text content"""
    print("🔍 Checking Document Index Content")
    print("=" * 50)
    
    try:
        # Load the index directly
        index_file = "document_index.json"
        if os.path.exists(index_file):
            with open(index_file, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
            
            print(f"📊 Index contains {len(index_data)} documents")
            
            # Check specific contraceptive documents
            contraceptive_files = [
                "GyaniNuxeo\\PD  72703 Compass - Contraceptives_Card NEW as of 12022024.docx",
                "GyaniNuxeo\\_CLIENT SUPPORT- MEMBER SERVICES St Joseph's Women's Contraceptive Coverage.docx"
            ]
            
            for file_path in contraceptive_files:
                if file_path in index_data:
                    doc = index_data[file_path]
                    print(f"\n📄 {os.path.basename(file_path)}")
                    print(f"   Title: {doc.get('title', 'N/A')}")
                    print(f"   Category: {doc.get('category', 'N/A')}")
                    
                    # Check if full_text exists and has content
                    full_text = doc.get('full_text', '')
                    if full_text and len(full_text.strip()) > 0:
                        print(f"   ✅ Has text content: {len(full_text)} characters")
                        print(f"   📝 Sample: {full_text[:200]}...")
                        
                        # Check for contraceptive content
                        if 'contraceptive' in full_text.lower():
                            print(f"   🎯 Contains 'contraceptive': YES")
                        else:
                            print(f"   🎯 Contains 'contraceptive': NO")
                    else:
                        print(f"   ❌ No text content found")
                else:
                    print(f"\n📄 {os.path.basename(file_path)}: NOT FOUND in index")
            
            # Count how many documents have actual text content
            docs_with_text = 0
            docs_without_text = 0
            
            for doc_path, doc_info in index_data.items():
                full_text = doc_info.get('full_text', '')
                if full_text and len(full_text.strip()) > 0:
                    docs_with_text += 1
                else:
                    docs_without_text += 1
            
            print(f"\n📊 Summary:")
            print(f"   Documents with text: {docs_with_text}")
            print(f"   Documents without text: {docs_without_text}")
            print(f"   Percentage with text: {(docs_with_text / len(index_data)) * 100:.1f}%")
            
        else:
            print(f"❌ Index file not found: {index_file}")
            
    except Exception as e:
        print(f"❌ Error checking index: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_document_index()