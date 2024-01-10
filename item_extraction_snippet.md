# Item extraction snippet
The code snippet I use to extract item data from sc2/Items.py into a json format is as follows. This goes at the bottom of Items.py, and the file is then run as a module with `python -m worlds.sc2.Items`

```python
if __name__ == '__main__':
    import json
    data = {
        item_name: {
            "type": item.type,
            "number": item.number,
            "race": item.race.name,
            "classification": item.classification.name,
            "quantity": item.quantity,
            "parent_item": item.parent_item,
            "origin": sorted(item.origin),
            "description": item.description,
        }
        for item_name, item in item_table.items()
    }
    with open('<path_to_repository>/data/item_data.json', 'w') as fp:
        json.dump(data, fp, indent=2)
```
