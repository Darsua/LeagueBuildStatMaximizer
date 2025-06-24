import json
from slpp import slpp as lua

with open('itemData.lua', 'r', encoding='utf-8') as f:
    data = f.read()

parsed = lua.decode(data)

with open('itemData.json', 'w', encoding='utf-8') as f:
    json.dump(parsed, f, ensure_ascii=False, indent=4)