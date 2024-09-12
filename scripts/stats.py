"""
Display some stats about the items
"""

import json
import os

ITEM_DATA_PATH = 'data/beta_item_data.json'

with open(ITEM_DATA_PATH, 'r') as fp:
    data = json.load(fp)

result = {}
zero_quantity_items = []

item_types = len(data)
for item_name, item_data in data.items():
    r = item_data['race']
    result.setdefault(r, 0)
    result[r] += item_data['quantity']
    if item_data['quantity'] == 0:
        zero_quantity_items.append(item_name)


print(f'Item types: {item_types}')
print(json.dumps(result, indent=2))
print(f'num 0-quantity items: {len(zero_quantity_items)}')
print(zero_quantity_items)
