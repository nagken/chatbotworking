import re

# Test text from the actual AI response (without extension)
test_text = 'Contraceptive coverage is separate from a health plan and requires a Contraceptives Card to be shown when ordering or picking up a prescription contraceptive. This card is requested from CVS Caremark. Individuals can talk with their doctor to review a list of no-cost contraceptives to decide which option is best for them. (Document 3: 106 29750e RxCard DM080718)'

print('Testing patterns with NO extension...')

# Test the pattern without extension requirement
pattern_no_ext = r'\(Document \d+: ([^)]+)\)'
matches = list(re.finditer(pattern_no_ext, test_text, re.IGNORECASE))
print(f'Pattern without extension found {len(matches)} matches:')
for i, match in enumerate(matches):
    filename = match.group(1).strip()
    print(f'  {i+1}. "{filename}"')
    print(f'     Full match: "{match.group(0)}"')
    print(f'     URL would be: /documents/{filename}')

# Test the pattern with extension requirement (should find 0)
pattern_with_ext = r'\(Document \d+: ([^)]+\.(?:docx?|pdf|xlsx?|pptx?))\)'
matches_ext = list(re.finditer(pattern_with_ext, test_text, re.IGNORECASE))
print(f'\nPattern with extension found {len(matches_ext)} matches:')