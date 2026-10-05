import json

with open("audit_details.json") as f:
    data = json.load(f)

for i, q in enumerate(data):
    if i+1 in [4, 9, 16, 17, 18]:
        print(f"Q{i+1}: {q['question']} -> {q['decision']}")
        for c in q['claims']:
            print(f"  {c['text']}")
