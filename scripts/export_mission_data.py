"""
Add Archipelago to the path for this to import data and print locally
"""

from worlds.sc2 import mission_groups, mission_tables

if __name__ == '__main__':
    import json
    group_data = {
        mission_group_name: mission_groups.mission_groups[mission_group_name]
        for mission_group_name in sorted(mission_groups.MissionGroupNames.get_all_group_names())
    }
    mission_data = {
        mission.mission_name: {
            'faction':
                'Terran' if mission_tables.MissionFlag.Terran in mission.flags
                else 'Zerg' if mission_tables.MissionFlag.Zerg in mission.flags
                else 'Protoss' if mission_tables.MissionFlag.Protoss in mission.flags
                else '',
            'campaign': mission.campaign.name.lower(),
        }
        for mission in mission_tables.SC2Mission
    }
    with open('data/mission_groups.json', 'w') as fp:
        json.dump(group_data, fp, indent=2)
    with open('data/mission_data.json', 'w') as fp:
        json.dump(mission_data, fp, indent=2)
