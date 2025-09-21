import re

# Test text from the actual AI response
test_text = 'Contraceptive coverage is separate from a health plan and requires a separate Contraceptives Card to be shown when ordering or picking up a prescription contraceptive. This card can be used at participating pharmacies. For questions, customers can call Customer Care toll-free at 1-888-924-8738. (Document 3: 106-29750e_RxCard_DM080718.pdf)'

print('Testing numbered document pattern...')
pattern = r'\(Document \d+: ([^)]+\.(?:docx?|pdf|xlsx?|pptx?))\)'
matches = list(re.finditer(pattern, test_text, re.IGNORECASE))
print(f'Found {len(matches)} matches:')
for i, match in enumerate(matches):
    filename = match.group(1).strip()
    print(f'  {i+1}. "{filename}"')
    print(f'     Full match: "{match.group(0)}"')
    print(f'     URL would be: /documents/{filename}')