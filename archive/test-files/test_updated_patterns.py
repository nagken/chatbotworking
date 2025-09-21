#!/usr/bin/env python3
"""
Test updated document link patterns
"""

import re

def test_patterns():
    # Actual text from the logs
    sample_text = """Contraceptive coverage is separate from a health plan and requires a separate Contraceptives Card to be shown when ordering or picking up a prescription contraceptive. This card can be used at participating pharmacies. For questions, customers can call Customer Care toll-free at 1-888-924-8738. (Document 3: 106-29750e_RxCard_DM080718.pdf)

For St. Joseph's Women's Contraceptive Coverage, a specific process is outlined for entering member information in RXCADS. This involves mirroring information from AS400, including effective dates and family types, but changing the Xwalk. The ID used for the main account needs to have 'WPS' added to the front when entering it into X3917 in RXCADS. (Document 2: CLIENT SUPPORT MEMBER SERVICES St Joseph's Women's Contraceptive Coverage.docx)"""

    print("🧪 Testing updated document patterns...")
    print(f"Sample text contains: {len(re.findall(r'Document \d+:', sample_text))} numbered document references")
    
    # Updated patterns
    patterns = [
        r'\(Document \d+: ([^)]+\.(?:docx?|pdf|xlsx?|pptx?))\)',  # "(Document 3: filename.ext)"
        r'\(Document: ([^)]+\.(?:docx?|pdf|xlsx?|pptx?))\)',      # "(Document: filename.ext)"
        r'Document \d+: ([^<\n)]+\.(?:docx?|pdf|xlsx?|pptx?))',   # "Document 3: filename.ext"
        r'Document: ([^<\n)]+\.(?:docx?|pdf|xlsx?|pptx?))',       # "Document: filename.ext"
        r'File: ([^<\n)]+\.(?:docx?|pdf|xlsx?|pptx?))',          # "File: filename.ext"
    ]
    
    for i, pattern in enumerate(patterns):
        print(f"\nPattern {i+1}: {pattern}")
        matches = list(re.finditer(pattern, sample_text, re.IGNORECASE))
        if matches:
            for j, match in enumerate(matches):
                filename = match.group(1).strip()
                print(f"  Match {j+1}: '{filename}'")
                print(f"    Full match: '{match.group(0)}'")
                print(f"    URL: /documents/{filename}")
        else:
            print("  No matches found")
    
    print(f"\nTotal document patterns found across all patterns: {sum(len(list(re.finditer(p, sample_text, re.IGNORECASE))) for p in patterns)}")

if __name__ == "__main__":
    test_patterns()