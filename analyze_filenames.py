#!/usr/bin/env python3

import json
import os
import urllib.parse

def analyze_filename_mismatches():
    """Analyze filename mismatches between index and actual files"""
    
    print("=== FILENAME MISMATCH ANALYSIS ===")
    
    # Load document index
    try:
        with open('document_index.json', 'r', encoding='utf-8') as f:
            index_data = json.load(f)
        print(f"✅ Loaded document index with {len(index_data)} documents")
    except Exception as e:
        print(f"❌ Failed to load document index: {e}")
        return
    
    # Get actual files from GyaniNuxeo
    actual_files = set()
    try:
        for filename in os.listdir('GyaniNuxeo'):
            actual_files.add(filename)
        print(f"✅ Found {len(actual_files)} actual files in GyaniNuxeo")
    except Exception as e:
        print(f"❌ Failed to list GyaniNuxeo files: {e}")
        return
    
    # Find contraceptive-related discrepancies
    print("\n=== CONTRACEPTIVE DOCUMENT ANALYSIS ===")
    
    contraceptive_index_files = []
    contraceptive_actual_files = []
    
    # From index
    for doc in index_data:
        filename = doc.get('filename', '')
        if 'contraceptive' in filename.lower() or 'client support' in filename.lower():
            contraceptive_index_files.append(filename)
    
    # From actual files
    for filename in actual_files:
        if 'contraceptive' in filename.lower() or 'client support' in filename.lower():
            contraceptive_actual_files.append(filename)
    
    print(f"\nIndex has {len(contraceptive_index_files)} contraceptive files:")
    for f in contraceptive_index_files:
        print(f"  INDEX: {f}")
    
    print(f"\nActual directory has {len(contraceptive_actual_files)} contraceptive files:")
    for f in contraceptive_actual_files:
        print(f"  ACTUAL: {f}")
    
    # Find character encoding issues
    print("\n=== CHARACTER ENCODING ISSUES ===")
    
    for index_file in contraceptive_index_files:
        # Find closest match in actual files
        best_match = None
        best_score = 0
        
        for actual_file in contraceptive_actual_files:
            # Simple similarity: count matching characters
            score = sum(1 for a, b in zip(index_file.lower(), actual_file.lower()) if a == b)
            if score > best_score:
                best_score = score
                best_match = actual_file
        
        if best_match and best_match != index_file:
            print(f"\n📝 MISMATCH FOUND:")
            print(f"   Index:  {repr(index_file)}")
            print(f"   Actual: {repr(best_match)}")
            
            # Show character differences
            for i, (a, b) in enumerate(zip(index_file, best_match)):
                if a != b:
                    print(f"   Diff at pos {i}: '{a}' vs '{b}' (ord {ord(a)} vs {ord(b)})")
                    break

if __name__ == "__main__":
    analyze_filename_mismatches()