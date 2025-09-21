#!/usr/bin/env python3

import json

# Check what documents are in the index
try:
    with open('document_index.json', 'r', encoding='utf-8') as f:
        index = json.load(f)
    
    print(f"Total documents: {len(index)}")
    
    # Look for the specific document we're testing
    test_file = "106-29750e_RxCard_DM080718.pdf"
    
    for i, doc in enumerate(index):
        if i < 5:  # Show first 5
            print(f"File: {doc.get('filename', 'NO FILENAME')}")
        
    # Search for our specific file
    found = [doc for doc in index if test_file in doc.get('filename', '')]
    if found:
        print(f"Found matching documents:")
        for doc in found:
            print(f"  Filename: {doc.get('filename')}")
            print(f"  Path: {doc.get('file_path')}")
    else:
        # Try partial match
        partial = [doc for doc in index if '106-29750e' in doc.get('filename', '')]
        print(f"Partial matches for '106-29750e':")
        for doc in partial[:3]:
            print(f"  Filename: {doc.get('filename')}")
            
except Exception as e:
    print(f"Error reading index: {e}")