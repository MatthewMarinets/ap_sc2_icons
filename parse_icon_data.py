"""
Parse Archipelago mod files to discover the linkage from item data to icon filename.
"""

# Client data: Item Name <--> Item ID
# * Item ID = (race, category, index)
# .galaxy file: Item ID --> Unlocks[]
# * Unlocks = (name, "upgrade"|"unit"|"ability")
# UpgradeData.xml: (name, "upgrade") --> icon?
# AbilData.xml: (name, "unit") <--> (name, "ability")
# * Note this name will be assembled from parts, e.g. AP_BarracksTrain,3
# * Sub-part may be Train, Build, Research, Ammo, Specialize, or 0
#   * this name does not matter for the assembled name; that number comes from ordering
# UnitData.xml: (name, "ability") --> (name, "button")
# ButtonData.xml: (name, "button") --> icon

from typing import *
import json
import os
import re
from datetime import datetime

class ItemId(NamedTuple):
    race: str
    category: str
    index: int

class GalaxyItem(NamedTuple):
    galaxy_type: Literal['unit', 'upgrade', 'ability']
    name: str

def get_item_data() -> dict[str, dict]:
    with open('data/item_data.json', 'r') as fp:
        return json.load(fp)

def get_item_numbers(item_data: dict[str, dict]) -> dict[str, ItemId]:
    return {
        item_name: ItemId(
            item['race'].lower(),
            item['type'].replace(' ', ''),
            item['number'])
        for item_name, item in item_data.items()
    }

def parse_galaxy_file(galaxy_path: str) -> Dict[ItemId, List[GalaxyItem]]:
    with open(galaxy_path, 'r') as fp:
        lines = fp.readlines()
    function_unlocks: dict[str, List[GalaxyItem]] = {}
    function_to_category: dict[str, ItemId] = {}
    unlocked_times = {}
    current_function = ''
    bit_array_line = -3
    race = ''
    category = ''
    function_name_pattern = re.compile(r'^void (\w+)')
    unlock_function_pattern = re.compile(r'libABFE498B_gf_AP_Triggers_unlock(Zerg|Terran|Protoss)(.*)')
    unlock_unit_pattern = re.compile(r'^\s*TechTreeUnitAllow\(lp_player,\s*"(AP_[^"]+)",\s*true\)')
    unlock_upgrade_pattern = re.compile(r'^\s*libNtve_gf_SetUpgradeLevelForPlayer\(lp_player,\s*"(AP_[^"]+)"')
    unlock_ability_pattern = re.compile(r'^\s*TechTreeAbilityAllow\(lp_player,\s*AbilityCommand\("(AP_[^"]+)",\s*\d+\),\s*true')
    UNLOCK_ARRAY_START = 'processBitsInBitArray'
    UNLOCK_PROGRESSIVE_ARRAY_START = 'ap_triggers_processUpgrades'
    is_progressive_array = False
    for line in lines:
        if match := re.match(function_name_pattern, line):
            current_function = match.group(1)
        elif UNLOCK_ARRAY_START in line:
            is_progressive_array = False
            bit_array_line += 1
            assert current_function
            match = re.match(unlock_function_pattern, current_function)
            race = match.group(1).lower()
            category = (match.group(2)
                .replace('Units', 'Unit')
                .replace('Units2', 'Unit2')
                .replace('Mercenaries', 'Mercenary')
                .replace('Buildings', 'Building')
                .replace('Upgrades', 'Upgrade')
                .replace('Upgrades2', 'Upgrade2')
                .replace('KerriganAbilities', 'Ability')
            )
        elif UNLOCK_PROGRESSIVE_ARRAY_START in line:
            is_progressive_array = True
            bit_array_line += 1
            assert current_function
            match = re.match(unlock_function_pattern, current_function)
            race = match.group(1).lower()
            category = (match.group(2)
                .replace('Upgrades', 'Upgrade')
                .replace('Upgrades2', 'Upgrade2')
            )
        elif bit_array_line > -3 and ')' not in line:
            assert race
            assert category
            if bit_array_line >= 0:
                function_name = line.split('//', 1)[0].strip().split(',', 1)[0]
                if 'Consumer_sig' not in function_name:
                    function_to_category[function_name] = ItemId(race, category, bit_array_line)
                bit_array_line += is_progressive_array
            bit_array_line += 1
        elif bit_array_line > -3:
            bit_array_line = -3
            race = ''
            category = ''
        elif line.startswith('}'):
            current_function = ''
        elif match := re.match(unlock_unit_pattern, line):
            assert current_function
            if 'DefaultTech' in current_function: continue
            function_unlocks.setdefault(current_function, []).append(GalaxyItem('unit', match.group(1)))
            unlocked_times.setdefault(match.group(1), 0)
            unlocked_times[match.group(1)] += 1
        elif match := re.match(unlock_upgrade_pattern, line):
            assert current_function
            if 'DefaultTech' in current_function: continue
            function_unlocks.setdefault(current_function, []).append(GalaxyItem('upgrade', match.group(1)))
            unlocked_times.setdefault(match.group(1), 0)
            unlocked_times[match.group(1)] += 1
        elif match := re.match(unlock_ability_pattern, line):
            assert current_function
            if 'DefaultTech' in current_function: continue
            function_unlocks.setdefault(current_function, []).append(GalaxyItem('ability', match.group(1)))
            unlocked_times.setdefault(match.group(1), 0)
            unlocked_times[match.group(1)] += 1
    result = {}
    for function, category in function_to_category.items():
        unlocks = function_unlocks[function]
        unlocks = [u for u in unlocks if unlocked_times[u.name] == 1]
        assert len(unlocks), f'function {function} has no unique items'
        result[category] = unlocks
    return result


def parse_upgrade_data(upgrade_data_path: str) -> Dict[str, str|None]:
    """upgrade -> icon"""
    with open(upgrade_data_path, 'r') as fp:
        lines = fp.readlines()
    result = {}
    current_upgrade = ''
    upgrade_start_pattern = re.compile(r'^\s*<CUpgrade[^\n]+id="(AP_[^"]+)"')
    icon_pattern = re.compile(r'^\s*<Icon value="([^"]+)"')
    for line in lines:
        if match := re.match(upgrade_start_pattern, line):
            current_upgrade = match.group(1)
            assert current_upgrade not in result
            result[current_upgrade] = None
        elif match := re.match(icon_pattern, line):
            current_icon = match.group(1)
            assert current_upgrade
            assert result[current_upgrade] is None
            result[current_upgrade] = current_icon
    return result

def parse_button_data(button_data_path: str) -> Dict[str, str|None]:
    """button -> icon"""
    with open(button_data_path, 'r') as fp:
        lines = fp.readlines()
    result = {}
    current_button = ''
    button_start_pattern = re.compile(r'^\s*<CButton id="([^"]+)"')
    icon_pattern = re.compile(r'^\s*<Icon value="([^"]+)"')
    for line in lines:
        if match := re.match(button_start_pattern, line):
            current_button = match.group(1)
            assert current_button not in result
            result[current_button] = None
        elif match := re.match(icon_pattern, line):
            current_icon = match.group(1)
            if not current_button:
                continue
            assert result[current_button] is None
            result[current_button] = current_icon
        elif '</CButton>' in line:
            current_button = ''
    return result

def parse_unit_data(unit_data_path: str) -> tuple[dict[str, list[str]], dict[str, str]]:
    """ability -> button, requirement -> button"""
    with open(unit_data_path, 'r') as fp:
        lines = fp.readlines()
    ability_to_button: dict[str, list[str]] = {}
    requirement_to_button: dict[str, str] = {}
    last_face = ''
    command_card_pattern = re.compile(r'^\s*<LayoutButtons.*Face="([^"]+)".*AbilCmd="(AP[^"]+)"')
    face_pattern = re.compile(r'^\s*<Face value="([^"]+)"/>')
    abilcmd_pattern = re.compile(r'^\s*<AbilCmd value="(AP_[^"]+)"/>')
    requirements_pattern = re.compile(r'\s*<Requirements\s*value="(AP_[^"]+)"/>')
    passive_pattern = re.compile(r'^\s*<LayoutButtons .*Face="([^"]+)".*Requirements="(AP_[^"]+)"')
    for line in lines:
        if match := re.match(command_card_pattern, line):
            face = match.group(1)
            ability = match.group(2)
            ability_to_button.setdefault(ability, [])
            if face not in ability_to_button[ability]:
                ability_to_button[ability].append(face)
            if ',' in ability:
                ability = ability.split(',', 1)[0]
                ability_to_button.setdefault(ability, [])
                if face not in ability_to_button[ability]:
                    ability_to_button[ability].append(face)
        elif match := re.match(face_pattern, line):
            last_face = match.group(1)
        elif match := re.match(requirements_pattern, line):
            assert last_face
            requirement_to_button[match.group(1)] = last_face
        elif match := re.match(passive_pattern, line):
            requirement_to_button[match.group(2)] = match.group(1)
        elif match := re.match(abilcmd_pattern, line):
            if not last_face:
                continue
            ability = match.group(1)
            ability_to_button.setdefault(ability, [])
            if last_face not in ability_to_button[ability]:
                ability_to_button[ability].append(last_face)
            if ',' in ability:
                ability = ability.split(',', 1)[0]
                ability_to_button.setdefault(ability, [])
                if last_face not in ability_to_button[ability]:
                    ability_to_button[ability].append(last_face)
        elif '</LayoutButtons>' in line:
            last_face = ''
    return (ability_to_button, requirement_to_button)

def parse_abil_data(abil_data_path: str) -> dict[str, list[str]]:
    """unit -> ability"""
    with open(abil_data_path, 'r') as fp:
        lines = fp.readlines()
    result: dict[str, list[str]] = {}
    current_ability_stem = ''
    current_ability_type = ''
    current_ability_index = 0
    train_start_pattern = re.compile(r'^\s*<CAbil(?:Warp)?Train\s+id="(AP_[^"]+)"')
    build_start_pattern = re.compile(r'^\s*<CAbilBuild\s+id="(AP_[^"]+)"')
    index_start_pattern = re.compile(r'^\s*<InfoArray\s+index="(Build|Train)(\d+)"(?:\s+Unit="(AP_[^"]+)")?')
    train_end_pattern = re.compile(r'^\s*</CAbil(?:Warp)?Train>')
    unit_pattern = re.compile(r'^\s*<Unit value="(AP_[^"]+)"/>')
    for line in lines:
        if match := re.match(train_start_pattern, line):
            assert not current_ability_type
            assert not current_ability_stem
            current_ability_index = 0
            current_ability_stem = match.group(1)
            current_ability_type = 'train'
        elif match := re.match(build_start_pattern, line):
            assert not current_ability_type
            assert not current_ability_stem
            current_ability_index = 0
            current_ability_stem = match.group(1)
            current_ability_type = 'build'
        elif match := re.match(index_start_pattern, line):
            assert current_ability_stem
            assert current_ability_type
            if current_ability_type == 'build':
                assert match.group(1) == 'Build'
                if match.group(3) is None:
                    continue
                unit = match.group(3)
                result.setdefault(unit, [])
                ability = f'{current_ability_stem},{int(match.group(2)) - 1}'
                ability_long = f'{current_ability_stem},{match.group(1)}{match.group(2)}'
                if ability in result[unit]:
                    continue
                result[unit].append(ability)
                result[unit].append(ability_long)
            else:
                current_ability_index = int(match.group(2)) - 1
        elif '</InfoArray>' in line and current_ability_type == 'train':
            current_ability_index = -1
        elif match := re.match(unit_pattern, line):
            assert current_ability_type == 'train'
            assert current_ability_stem
            result.setdefault(match.group(1), [])
            assert current_ability_index >= 0
            ability = f'{current_ability_stem},{current_ability_index}'
            ability_long = f'{current_ability_stem},Train{current_ability_index+1}'
            if ability in result[match.group(1)]:
                # Mercs, zerglings, scourge
                continue
            result[match.group(1)].append(ability)
            result[match.group(1)].append(ability_long)
        elif '</CAbilBuild>' in line:
            assert current_ability_type == 'build'
            current_ability_type = ''
            current_ability_stem = ''
            current_ability_index = 0
        elif re.match(train_end_pattern, line):
            assert current_ability_type == 'train'
            current_ability_type = ''
            current_ability_stem = ''
            current_ability_index = 0
    return result

def parse_requirement_data(requirement_data_path: str) -> dict[str, List[str]]:
    """requirement -> requirement_node"""
    with open(requirement_data_path, 'r') as fp:
        lines = fp.readlines()
    requirement_to_node: dict[str, str] = {}
    current_req = ''
    requirement_start_pattern = re.compile(r'^\s*<CRequirement\s+id="(AP_[^"]+)">')
    node_pattern = re.compile(r'^\s*<NodeArray.*Link="(AP_[^"]+)"')
    for line in lines:
        if match := re.match(requirement_start_pattern, line):
            current_req = match.group(1)
        elif match := re.match(node_pattern, line):
            if not current_req:
                continue
            requirement_to_node.setdefault(current_req, [])
            if match.group(1) not in requirement_to_node[current_req]:
                requirement_to_node[current_req].append(match.group(1))
        elif '</CRequirement>' in line:
            current_req = ''
    return requirement_to_node

def parse_combined_requirement_data(requirement_data_path: str, requirement_node_data_path: str) -> dict[str, str]:
    """upgrade -> requirement"""
    with open(requirement_node_data_path, 'r') as fp:
        lines = fp.readlines()
    requirement_node_to_upgrade: dict[str, str] = {}
    requirement_node_interlink: dict[str, List[str]] = {}
    UPGRADE = 'upgrade'
    current_requirement = ()

    upgrade_start_pattern = re.compile(r'^\s*<CRequirementCountUpgrade\s+id="(AP_[^"]+)">')
    other_requirement_start_pattern = re.compile(r'^\s*<(CRequirement\w+)\s+id="(AP_[^"]+)"[^/]+$')
    count_pattern = re.compile(r'^\s*<Count Link="(AP_[^"]+)" State="CompleteOnly"')
    operand_pattern = re.compile(r'^\s*<OperandArray .*value="(AP_[^"]+)"')
    upgrade_end_pattern = re.compile(r'^\s*</CRequirementCountUpgrade>')
    other_req_end_pattern = re.compile(r'^\s*</(CRequirement\w+)>')
    for line_number, line in enumerate(lines):
        if match := re.match(upgrade_start_pattern, line):
            assert not current_requirement
            current_requirement = (match.group(1), UPGRADE)
        elif match := re.match(upgrade_end_pattern, line):
            if current_requirement: assert current_requirement[1] == UPGRADE
            current_requirement = ()
        elif match := re.match(other_requirement_start_pattern, line):
            assert not current_requirement
            current_requirement = (match.group(2), match.group(1))
        elif match := re.match(other_req_end_pattern, line):
            if current_requirement: assert current_requirement[1] == match.group(1)
            current_requirement = ()
        elif match := re.match(count_pattern, line):
            assert current_requirement
            if current_requirement[1] != UPGRADE:
                continue
            assert current_requirement[0] not in requirement_node_to_upgrade
            requirement_node_to_upgrade[current_requirement[0]] = match.group(1)
        elif match := re.match(operand_pattern, line):
            assert current_requirement
            assert current_requirement[1] != UPGRADE
            requirement_node_interlink.setdefault(current_requirement, []).append(match.group(1))
    requirement_to_node = parse_requirement_data(requirement_data_path)
    upgrade_to_requirement: dict[str, set[str]] = {}
    for requirement, start_nodes in requirement_to_node.items():
        nodes = set()
        for node in start_nodes:
            nodes.update(accessible_nodes(node, requirement_node_interlink))
        nodes = sorted(nodes)
        for node in nodes:
            upgrade = requirement_node_to_upgrade.get(node)
            if upgrade is not None:
                upgrade_to_requirement.setdefault(upgrade, set()).add(requirement)

    return {upgrade: sorted(reqs) for upgrade, reqs in upgrade_to_requirement.items()}

def accessible_nodes(start: str, map: dict[str, list[str]]) -> list[str]:
    result = set([start])
    descendants = map.get(start, [])
    for descendant in descendants:
        result.update(accessible_nodes(descendant, map))
    return result

def resolve_item_icon(
    item: ItemId,
    id_to_unlocks: dict[ItemId, List[GalaxyItem]],
    unit_to_ability: dict[str, List[str]],
    ability_to_button: dict[str, List[str]],
    button_to_icon: dict[str, str],
    upgrade_to_icon: dict[str, str],
    requirement_to_button: dict[str, str],
    upgrade_to_requirement: dict[str, list[str]]
) -> list[str]:
    result: set[str] = set()
    unlocks = id_to_unlocks.get(item, [])
    for unlock in unlocks:
        if unlock.galaxy_type == 'unit':
            abilities = unit_to_ability.get(unlock.name)
            if not abilities:
                continue
            buttons = set()
            for ability in abilities:
                buttons.update(ability_to_button.get(ability, []))
            for button in buttons:
                icon = button_to_icon.get(button)
                if icon:
                    result.add(icon.lower())
        elif unlock.galaxy_type == 'upgrade':
            # Check if the upgrade direct-links to an icon
            icon = upgrade_to_icon.get(unlock.name)
            if icon:
                result.add(icon.lower())
            # Check if a button direct-links to an upgrade
            icon = button_to_icon.get(unlock.name)
            if icon:
                result.add(icon.lower())
            # Passives, analyze if a requirement reveals a command-card button
            requirements = upgrade_to_requirement.get(unlock.name, [])
            for requirement in requirements:
                button = requirement_to_button.get(requirement)
                if button:
                    icon = button_to_icon.get(button)
                    if icon:
                        result.add(icon.lower())
        elif unlock.galaxy_type == 'ability':
            buttons = ability_to_button[unlock.name]

            for button in buttons:
                icon = button_to_icon.get(button)
                if icon:
                    result.add(icon.lower())
    return [x.replace('&apos;', "'") for x in sorted(result)]


def main():
    with open('workspace.json', 'r') as fp:
        config = json.load(fp)
    game_data = os.path.join(config['mod_files'], 'Mods/ArchipelagoPlayer.SC2Mod/Base.SC2Data/GameData')
    liberty_game_data = config.get('liberty_game_data')

    item_data = get_item_data()
    item_numbers = get_item_numbers(item_data)
    upgrade_to_icon = parse_upgrade_data(os.path.join(game_data, 'UpgradeData.xml'))
    button_to_icon = parse_button_data(os.path.join(game_data, 'ButtonData.xml'))
    if liberty_game_data:
        vanilla_button_icons = parse_button_data(os.path.join(liberty_game_data, 'ButtonData.xml'))
        button_to_icon.update(vanilla_button_icons)
    id_to_unlocks = parse_galaxy_file(os.path.join(config['mod_files'], 'Mods/ArchipelagoTriggers.SC2Mod/Base.SC2Data/LibABFE498B.galaxy'))
    unit_to_ability = parse_abil_data(os.path.join(game_data, 'AbilData.xml'))
    ability_to_button, requirement_to_button = parse_unit_data(os.path.join(game_data, 'UnitData.xml'))
    upgrade_to_requirement = parse_combined_requirement_data(os.path.join(game_data, 'RequirementData.xml'), os.path.join(game_data, 'RequirementNodeData.xml'))

    upgrade_to_icon = {key: value for key, value in upgrade_to_icon.items() if value is not None}
    button_to_icon = {key: value for key, value in button_to_icon.items() if value is not None}
    kwargs = {
        'id_to_unlocks': id_to_unlocks,
        'unit_to_ability': unit_to_ability,
        'ability_to_button': ability_to_button,
        'button_to_icon': button_to_icon,
        'upgrade_to_icon': upgrade_to_icon,
        'requirement_to_button': requirement_to_button,
        'upgrade_to_requirement': upgrade_to_requirement,
    }
    # resolve_item_icon(item_numbers['Incinerator Gauntlets (Firebat)'], id_to_unlocks, unit_to_ability, ability_to_button, button_to_icon, upgrade_to_icon)

    found = 0
    locations = {}
    for item_name, item in item_numbers.items():
        icon_paths = resolve_item_icon(item, **kwargs)
        if icon_paths: found += 1
        locations[item_name] = icon_paths
    result = {
        'meta': {
            'timestamp': datetime.now().strftime('%Y-%m-%d'),
            'items': len(item_numbers),
            'located': found,
        },
        'locations': locations,
    }
    print(f'Found {found} / {len(item_numbers)}')
    with open('data/locations.json', 'w') as fp:
        json.dump(result, fp, indent=2)

if __name__ == '__main__':
    main()
    
