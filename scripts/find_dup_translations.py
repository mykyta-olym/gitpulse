"""Find duplicate translation values in sk.json (3+ keys with same value)."""

import json
from collections import Counter

with open("src/app/i18n/catalogs/sk.json", encoding="utf-8") as f:
    d = json.load(f)

val_count = Counter(d.values())
dupes = {v: [k for k, vv in d.items() if vv == v] for v, c in val_count.items() if c >= 3}
for val, keys in sorted(dupes.items(), key=lambda x: -len(x[1])):
    print(f'  [{len(keys)}x] "{val}"')
    for k in keys[:5]:
        print(f'    - "{k}"')
    if len(keys) > 5:
        print(f"    ... +{len(keys) - 5} more")
print(f"\nTotal groups with 3+ same value: {len(dupes)}")
