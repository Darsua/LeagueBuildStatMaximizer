import json
import pandas as pd
import re
import copy

with open('itemData.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    print(f"Loaded {len(data)} items from itemData.json.\n")

def resolve_references(data_ref):
    def resolve_value(value_ref, ref_item, key_ref=None):
        if isinstance(value_ref, str) and value_ref.startswith("=>"):
            print(f"Resolving reference for {ref_item}: {key_ref} {value_ref}")
            ref_item_name = value_ref[2:].strip()
            ref_item = data_ref.get(ref_item_name)
            if ref_item is None or key_ref is None:
                return None
            return copy.deepcopy(ref_item.get(key_ref))
        elif isinstance(value_ref, dict):
            return {k: resolve_value(v, ref_item, k) for k, v in value_ref.items()}
        elif isinstance(value_ref, list):
            return [resolve_value(v, ref_item) for v in value_ref]
        else:
            return value_ref

    for item_to_check, info in data_ref.items():
        for key, value in list(info.items()):
            if isinstance(value, str) and value.startswith("=>"):
                print (f"Resolving reference for {item_to_check}: {key} {value}")
                ref_name = value[2:].strip()
                ref = data_ref.get(ref_name)
                if ref is not None and key in ref:
                    info[key] = copy.deepcopy(ref[key])
            elif isinstance(value, dict):
                # noinspection PyTypeChecker
                info[key] = resolve_value(value, item_to_check, key)
            elif isinstance(value, list):
                info[key] = [resolve_value(v, item_to_check) for v in value]

# Process derived data
resolve_references(data)
resolve_references(data)
resolve_references(data)
print("References resolved.\n")

# Remove non-rift items
to_remove = [
    item for item, info in data.items()
    if info.get('modes').get("classic sr 5v5") == False
]
for item in to_remove:
    print(f"Removing non-rift item: {item}, Modes: {data[item].get('modes')}")
    del data[item]
print(f"Removed {len(to_remove)} non-rift items.\n")

# Remove non-player shop stat giving items
allowed_types = {'Starter', 'Basic', 'Epic', 'Legendary', 'Boots'}
to_remove = [
    item for item, info in data.items()
    if not any(t in allowed_types for t in (info.get('type') if isinstance(info.get('type'), list) else [info.get('type')]))
]
for item in to_remove:
    print(f"Removing non-player shop stat giving item: {item}, Type: {data[item].get('type')}")
    del data[item]
print(f"Removed {len(to_remove)} non-player shop stat giving items.\n")

# Remove distributed tag
for item, info in data.items():
    item_type = info.get('type')
    if isinstance(item_type, list) and 'distributed' in [t.lower() for t in item_type]:
        print(f"Removing 'distributed' from item: {item}, Type: {item_type}")
        info['type'] = [t for t in item_type if t.lower() != 'distributed']
    elif isinstance(item_type, str) and item_type.lower() == 'distributed':
        print(f"Removing 'distributed' from item: {item}, Type: {item_type}")
        info['type'] = None
print("Removed 'distributed' tag from items.\n")

# Convert item types from list to string
for item, info in data.items():
    item_type = info.get('type')
    if isinstance(item_type, list):
        # Join list elements with comma if multiple types, or just take the first
        info['type'] = ', '.join(item_type)
print("Converted item types from list to string.\n")

# Process items stats
def extract_adaptive_x(spec):
    match = re.match(r'\+\{\{adaptive\|(\d+)}}', spec)
    if match:
        return int(match.group(1))
    return None

def extract_health_on_hit(spec):
    match = re.match(r'\+(\d+)\s+\[\[health]]\s+\[\[on-hit]]', spec)
    if match:
        return int(match.group(1))
    return None

for item in data:
    stats = data[item].get('stats')
    if stats:
        # Special stats
        if 'spec' in stats:
            # Adaptive power
            adaptive_x = extract_adaptive_x(stats['spec'])
            if adaptive_x is not None:
                print(f"Special stat: {item}, Adaptive power: {adaptive_x}")
                stats['ap'] = stats.get('ap', 0) + adaptive_x
                stats['ad'] = stats.get('ad', 0) + adaptive_x

            # Health on hit
            health_on_hit = extract_health_on_hit(stats['spec'])
            if health_on_hit is not None:
                print(f"Special stat for item: {item}, Health on Hit: {health_on_hit}")
                stats['lifesteal'] = stats.get('lifesteal', 0) + health_on_hit

            del stats['spec']

# Build a DataFrame from item stats and include 'type', 'itemlimit'
df = pd.DataFrame.from_dict(
    {
        item: {
            'type': info.get('type'),
            'itemlimit': [info.get('itemlimit'), info.get('itemlimit2')] if 'itemlimit2' in info else [info.get('itemlimit')],
            'cost' : info.get('buy', 0),
            **info.get('stats', {})
        }
        for item, info in data.items()
    },
    orient='index'
)

df.index.name = 'name'  # Set index name to 'name'
df.reset_index(inplace=True)  # Move index to a column
df.sort_values("name", inplace=True)  # Sort by name column

# Fill NaN values with 0
df.fillna(0, inplace=True)

# Write to file in CSV format
df.to_csv('itemData.csv', encoding='utf-8-sig', index=False)
print(f"\nWritten {len(df)} items to itemData.csv.")
