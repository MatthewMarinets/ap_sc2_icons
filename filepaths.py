from dataclasses import dataclass

@dataclass
class Paths:
    workspace: str = 'workspace.json'

    overrides: str = 'data/overrides.json'
    icon_paths: str = 'data/locations.json'
    icon_manifest: str = 'data/icon_manifest.json'
    item_data: str = 'data/item_data.json'
    item_groups: str = 'data/item_groups.json'
    mission_data: str = 'data/mission_data.json'
    mission_groups: str = 'data/mission_groups.json'

    items_html: str = 'index.html'
    item_groups_html: str = 'itemgroups.html'
    mission_groups_html: str = 'missiongroups.html'
