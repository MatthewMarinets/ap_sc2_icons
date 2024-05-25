"""
Add Archipelago to the path for this to import data and print locally
"""

from worlds.sc2 import item_descriptions, item_groups, items

if __name__ == '__main__':
    import json
    data = {
        item_name: {
            "type": item.type.name.replace('_', ' ').title(),
            "number": item.number,
            "race": item.race.name,
            "classification": item.classification.name,
            "quantity": item.quantity,
            "parent_item": item.parent_item,
            "description": item_descriptions.item_descriptions[item_name],
        }
        for item_name, item in items.item_table.items()
    }
    item_groups = {
        item_group_name: item_group
        for item_group_name, item_group in item_groups.item_name_groups.items()
        if item_group_name not in item_groups.unlisted_item_name_groups
    }
    with open('data/item_data.json', 'w') as fp:
        json.dump(data, fp, indent=2)
    with open('data/item_groups.json', 'w') as fp:
        json.dump(item_groups, fp, indent=2)
