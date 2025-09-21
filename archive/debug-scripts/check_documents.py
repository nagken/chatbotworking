#!/usr/bin/env python3

import json
import os

# Load document index
with open('document_index.json', 'r', encoding='utf-8') as f:
    documents = json.load(f)

print(f"Total documents indexed: {len(documents)}")
print("\nFirst 10 documents:")
for i, doc in enumerate(documents[:10]):
    print(f"{i+1}: {doc['filename']}")

# Look for contraceptive-related documents
print("\n=== CONTRACEPTIVE-RELATED DOCUMENTS ===")
contraceptive_docs = []
for i, doc in enumerate(documents):
    filename = doc['filename'].lower()
    if 'contraceptive' in filename or 'rxcard' in filename or '29750' in filename:
        contraceptive_docs.append((i+1, doc['filename']))

print(f"Found {len(contraceptive_docs)} contraceptive-related documents:")
for index, filename in contraceptive_docs:
    print(f"  {index}: {filename}")

# Check specific documents mentioned in the AI response
print("\n=== CHECKING SPECIFIC DOCUMENTS FROM AI RESPONSE ===")
target_docs = [
    "106-29750e_RxCard_DM080718.pdf",
    "_CLIENT SUPPORT- MEMBER SERVICES St Joseph's Women's Contraceptive Coverage.docx"
]

for target in target_docs:
    found = False
    for i, doc in enumerate(documents):
        if target in doc['filename']:
            print(f"✅ FOUND: {target} -> {doc['filename']}")
            found = True
            break
    if not found:
        print(f"❌ NOT FOUND: {target}")

print("\n=== DOCUMENT CONTENT PREVIEW ===")
# Check content of contraceptive docs
for index, filename in contraceptive_docs[:3]:  # First 3 only
    doc = documents[index-1]
    print(f"\nDocument: {filename}")
    print(f"Content preview: {doc.get('content', 'No content')[:200]}...")