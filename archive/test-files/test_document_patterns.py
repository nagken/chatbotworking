#!/usr/bin/env python3
"""
Test document link extraction patterns
"""

import re
import urllib.parse

def test_document_link_extraction():
    # Sample text from the AI response
    sample_text = """Contraceptive coverage is a separate benefit from a health plan that requires the presentation of a Contraceptives Card when ordering or picking up prescription contraceptives. This card allows access to a list of no-cost contraceptives. Employees are trained on how to handle private health information related to this coverage. (Document: 106 29750e RxCard DM080718.pdf)

For St. Joseph's Women's Contraceptive Coverage, the process involves mirroring information from AS400 to RXCADS under X3917, specifically the Account and Group number for X0247. The carrier code and ID/Xwalk are changed, with "WPS" added to the front of the main account ID. Effective dates and family types are mirrored from AS400, with only the Xwalk needing to be changed. (Document: CLIENT SUPPORT MEMBER SERVICES St Joseph's Women's Contraceptive Coverage.docx)"""
    
    print("🧪 Testing document link extraction patterns...")
    print(f"Sample text length: {len(sample_text)}")
    print("\n" + "="*80)
    print("SAMPLE TEXT:")
    print("="*80)
    print(sample_text)
    print("\n" + "="*80)
    
    # Current patterns from the code
    doc_patterns = [
        r'Document \d+: ([^<\n]+?)(?:\n|<br>|$)',  # "Document 1: Title"
        r'File: ([^<\n]+\.(?:docx?|pdf|xlsx?|pptx?))',  # "File: filename.docx"
        r'([^<\n\s]+\.(?:docx?|pdf|xlsx?|pptx?))',  # Any filename with extension
    ]
    
    # Test current patterns
    print("TESTING CURRENT PATTERNS:")
    print("="*50)
    
    for i, pattern in enumerate(doc_patterns):
        print(f"\nPattern {i+1}: {pattern}")
        matches = re.finditer(pattern, sample_text, re.IGNORECASE)
        match_count = 0
        for match in matches:
            match_count += 1
            print(f"  Match {match_count}: '{match.group(1) if match.groups() else match.group(0)}'")
            print(f"    Full match: '{match.group(0)}'")
            print(f"    Position: {match.start()}-{match.end()}")
        
        if match_count == 0:
            print("  No matches found")
    
    # Test improved patterns
    print("\n" + "="*50)
    print("TESTING IMPROVED PATTERNS:")
    print("="*50)
    
    improved_patterns = [
        r'\(Document: ([^)]+\.(?:docx?|pdf|xlsx?|pptx?))\)',  # "(Document: filename.ext)"
        r'Document: ([^<\n)]+\.(?:docx?|pdf|xlsx?|pptx?))',   # "Document: filename.ext"
        r'File: ([^<\n)]+\.(?:docx?|pdf|xlsx?|pptx?))',      # "File: filename.ext"
    ]
    
    for i, pattern in enumerate(improved_patterns):
        print(f"\nImproved Pattern {i+1}: {pattern}")
        matches = re.finditer(pattern, sample_text, re.IGNORECASE)
        match_count = 0
        for match in matches:
            match_count += 1
            filename = match.group(1).strip()
            print(f"  Match {match_count}: '{filename}'")
            print(f"    Full match: '{match.group(0)}'")
            print(f"    URL would be: /documents/{urllib.parse.quote(filename)}")
        
        if match_count == 0:
            print("  No matches found")

if __name__ == "__main__":
    test_document_link_extraction()