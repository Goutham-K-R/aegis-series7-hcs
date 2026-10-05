import json
with open('audit_details.json') as f:
    data = json.load(f)
for i, q in enumerate(data):
    if q['decision'] == 'VERIFIED' or i+1 == 2:
        print(f"Q{i+1}: {q['decision']}")
