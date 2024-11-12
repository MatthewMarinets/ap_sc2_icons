"""
Add Archipelago to the path for this to import data and print locally
"""

from worlds.sc2.item import item_descriptions, item_groups, item_tables

if __name__ == '__main__':
    import json
    import sys
    if len(sys.argv) < 2:
        item_data_path = 'data/item_data.json'
    else:
        item_data_path = sys.argv[1]
    if len(sys.argv) < 3:
        item_groups_path = 'data/item_groups.json'
    else:
        item_groups_path = sys.argv[2]
    if len(sys.argv) < 4:
        key_data_path = 'data/key_data.json'
    else:
        key_data_path = sys.argv[3]

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
        for item_name, item in item_tables.item_table.items()
        if item_name not in item_tables.key_item_table
    }
    key_data = list(item_tables.key_item_table)
    
    item_groups = {
        item_group_name: item_groups.item_name_groups[item_group_name]
        for item_group_name in sorted(item_groups.ItemGroupNames.get_all_group_names())
    }
    with open(item_data_path, 'w') as fp:
        json.dump(data, fp, indent=2)
    with open(item_groups_path, 'w') as fp:
        json.dump(item_groups, fp, indent=2)
    with open(key_data_path, 'w') as fp:
        json.dump(key_data, fp, indent=2)
