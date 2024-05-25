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
                .replace('ProgressiveUpgrades', 'Progressive')
                .replace('Upgrades', 'Upgrade')
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

def parse_unit_data(unit_data_path: str) -> tuple[dict[str, list[str]], dict[str, set[str]]]:
    """ability -> button, requirement -> button"""
    with open(unit_data_path, 'r') as fp:
        lines = fp.readlines()
    ability_to_button: dict[str, list[str]] = {}
    requirement_to_button: dict[str, set[str]] = {}
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
            requirement_to_button.setdefault(match.group(1), set()).add(last_face)
        elif match := re.match(passive_pattern, line):
            requirement_to_button.setdefault(match.group(2), set()).add(match.group(1))
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

def parse_behaviour_data(behaviour_data_path: str) -> dict[str, str]:
    """validator -> icon"""
    with open(behaviour_data_path, 'r') as fp:
        lines = fp.readlines()
    validator_to_icon: dict[str, str] = {}

    icon_pattern = re.compile(r'^\s*<InfoIcon value="([^"]+)"')
    behaviour_start_pattern = re.compile(r'^\s*<CBehaviorBuff id="(AP_[^"]+)"')
    behaviour_end_pattern = re.compile(r'^\s*</CBehaviorBuff>')
    validator_pattern = re.compile(r'^\s*<DisableValidatorArray value="(AP_[^"]+)"')
    hidden_pattern = re.compile(r'^\s*<InfoFlags index="Hidden" value="1"/>')

    current_behaviour = ''
    current_validator = ''
    current_icon = ''
    hidden = False
    for line in lines:
        if match := re.match(behaviour_start_pattern, line):
            current_behaviour = match.group(1)
        elif match := re.match(icon_pattern, line):
            current_icon = match.group(1)
        elif match := re.match(validator_pattern, line):
            current_validator = match.group(1)
        elif match := re.match(hidden_pattern, line):
            hidden = True
        elif match := re.match(behaviour_end_pattern, line):
            if current_behaviour and current_validator and current_icon and not hidden:
                validator_to_icon[current_validator] = current_icon.lower()
            current_behaviour = ''
            current_validator = ''
            current_icon = ''
            hidden = False
    return validator_to_icon

def parse_validator_data(validator_data_path: str) -> dict[str, str]:
    """requirement -> validator"""
    with open(validator_data_path, 'r') as fp:
        lines = fp.readlines()
    requirement_to_validator: dict[str, str] = {}
    validator_start_pattern = re.compile(r'^\s*<CValidatorPlayerRequirement id="(AP_[^"]+)"')
    validator_end_pattern = re.compile(r'^\s*</CValidatorPlayerRequirement>')
    requirement_pattern = re.compile(r'^\s*<Value value="(AP_[^"]+)"')
    is_positive_pattern = re.compile(r'^\s*<Find value="1"/>')

    current_validator = ''
    current_requirement = ''
    is_positive = False
    for line in lines:
        if match := re.match(validator_start_pattern, line):
            if match.group(1) != 'AP_HaveKerriganPrimalRage':
                current_validator = match.group(1)
        elif match := re.match(requirement_pattern, line):
            if not current_validator: continue
            current_requirement = match.group(1)
        elif match := re.match(is_positive_pattern, line):
            is_positive = True
        elif match := re.match(validator_end_pattern, line):
            if current_requirement and current_validator and is_positive:
                assert current_requirement not in requirement_to_validator
                requirement_to_validator[current_requirement] = current_validator
            current_validator = ''
            current_requirement = ''
            is_positive = False
    return requirement_to_validator


def parse_abil_data(abil_data_path: str) -> tuple[dict[str, list[str]], dict[str, list[str]], dict[str, list[str]]]:
    """unit -> ability (train), requirement -> button, requirement -> ability"""
    with open(abil_data_path, 'r') as fp:
        lines = fp.readlines()
    unit_to_ability: dict[str, list[str]] = {}
    requirement_to_button: dict[str, list[str]] = {}
    requirement_to_ability: dict[str, list[str]] = {}
    current_ability_stem = ''
    current_ability_type = ''
    current_ability_index = 0

    train_start_pattern = re.compile(r'^\s*<CAbil(?:Warp)?Train\s+id="(AP_[^"]+)">')
    build_start_pattern = re.compile(r'^\s*<CAbilBuild\s+id="(AP_[^"]+)"')
    other_abil_start_pattern = re.compile(r'^\s*<CAbil\w+\s+id="(AP_[^"]+)"[^/]+$')
    index_start_pattern = re.compile(r'^\s*<InfoArray\s+index="(Build|Train)(\d+)"(?:\s+Unit="(AP_[^"]+)")?')
    button_pattern = re.compile(r'^\s*<CmdButtonArray (?:index="([^"]+)" )?.*(?:DefaultButtonFace="([^"]+)" )?.*Requirements="(AP_[^"]+)"')
    abil_end_pattern = re.compile(r'^\s*</CAbil(\w+)>')
    unit_pattern = re.compile(r'^\s*<Unit value="(AP_[^"]+)"/>')
    default_button_pattern = re.compile(r'^\s*<Button DefaultButtonFace="(AP_[^"]+)" .*Requirements="(AP_[^"]+)"')
    for line_number, line in enumerate(lines):
        if match := re.match(train_start_pattern, line):
            assert not current_ability_type, f"Error on line {line_number}: '{line}'"
            assert not current_ability_stem, f"Error on line {line_number}: '{line}'"
            current_ability_index = 0
            current_ability_stem = match.group(1)
            current_ability_type = 'train'
        elif match := re.match(build_start_pattern, line):
            assert not current_ability_type
            assert not current_ability_stem
            current_ability_index = 0
            current_ability_stem = match.group(1)
            current_ability_type = 'build'
        elif match := re.match(other_abil_start_pattern, line):
            assert not current_ability_type
            assert not current_ability_stem
            current_ability_index = 0
            current_ability_stem = match.group(1)
            current_ability_type = 'other'
        elif match := re.match(index_start_pattern, line):
            assert current_ability_stem
            assert current_ability_type
            if current_ability_type == 'build':
                assert match.group(1) == 'Build'
                if match.group(3) is None:
                    continue
                unit = match.group(3)
                unit_to_ability.setdefault(unit, [])
                ability = f'{current_ability_stem},{int(match.group(2)) - 1}'
                ability_long = f'{current_ability_stem},{match.group(1)}{match.group(2)}'
                if ability in unit_to_ability[unit]:
                    continue
                unit_to_ability[unit].append(ability)
                unit_to_ability[unit].append(ability_long)
            elif current_ability_type == 'train':
                current_ability_index = int(match.group(2)) - 1
            # Note(mm): not handling info arrays for 'other' abilities
        elif match := re.match(button_pattern, line):
            assert match.group(1) or match.group(2)
            if match.group(2):
                requirement_to_button.setdefault(match.group(3), []).append(match.group(2))
            if match.group(1):
                if not current_ability_stem: continue
                assert current_ability_type == 'other'
                requirement_to_ability.setdefault(match.group(3), []).extend([
                    f'{current_ability_stem},{match.group(1)}',
                    f'{current_ability_stem},{current_ability_index}',
                ])
                current_ability_index += 1
        elif match := re.match(default_button_pattern, line):
            requirement_to_button.setdefault(match.group(2), []).append(match.group(1))
        elif '</InfoArray>' in line and current_ability_type == 'train':
            current_ability_index = -1
        elif match := re.match(unit_pattern, line):
            assert current_ability_type == 'train'
            assert current_ability_stem
            unit_to_ability.setdefault(match.group(1), [])
            assert current_ability_index >= 0
            ability = f'{current_ability_stem},{current_ability_index}'
            ability_long = f'{current_ability_stem},Train{current_ability_index+1}'
            if ability in unit_to_ability[match.group(1)]:
                # Mercs, zerglings, scourge
                continue
            unit_to_ability[match.group(1)].append(ability)
            unit_to_ability[match.group(1)].append(ability_long)
        elif match := re.match(abil_end_pattern, line):
            current_ability_type = ''
            current_ability_stem = ''
            current_ability_index = 0
    return unit_to_ability, requirement_to_button, requirement_to_ability

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
            assert current_requirement, f'Error on line {line_number}: found count outside requirement'
            if current_requirement[1] != UPGRADE:
                continue
            assert current_requirement[0] not in requirement_node_to_upgrade, f"{current_requirement[0]} is already associated with an upgrade"
            requirement_node_to_upgrade[current_requirement[0]] = match.group(1)
        elif match := re.match(operand_pattern, line):
            assert current_requirement
            assert current_requirement[1] != UPGRADE
            requirement_node_interlink.setdefault(current_requirement[0], []).append(match.group(1))
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
    item_name: str,
    item_numbers: dict[str, ItemId],
    id_to_unlocks: dict[ItemId, List[GalaxyItem]],
    unit_to_ability: dict[str, List[str]],
    ability_to_button: dict[str, List[str]],
    button_to_icon: dict[str, str],
    upgrade_to_icon: dict[str, str],
    requirement_to_button: dict[str, set[str]],
    requirement_to_ability: dict[str, set[str]],
    upgrade_to_requirement: dict[str, list[str]],
    requirement_to_validator: dict[str, str],
    validator_to_icon: dict[str, str],
    overrides: dict,
) -> list[str]:
    result: set[str] = set()
    item = item_numbers[item_name]
    if item_name in overrides['set']:
        return overrides['set'][item_name]
    if item_name in overrides['add']:
        result.update(overrides['add'][item_name])
    for pattern in overrides['pattern_add']:
        if re.match(pattern, item_name):
            result.update(overrides['pattern_add'][pattern])
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
                # Check behaviour icons through validators
                icon = validator_to_icon.get(requirement_to_validator.get(requirement))
                if icon:
                    result.add(icon)
                # Check default ability icons through requirements
                buttons = sorted(requirement_to_button.get(requirement, []))
                # Check non-default ability icons through requirements and unit command-cards
                abilities = sorted(requirement_to_ability.get(requirement, []))
                for ability in abilities:
                    buttons.extend(ability_to_button.get(ability, []))
                for button in buttons:
                    icon = button_to_icon.get(button)
                    if icon:
                        result.add(icon.lower())
                    ability_to_button
        elif unlock.galaxy_type == 'ability':
            buttons = ability_to_button.get(unlock.name, [])

            for button in buttons:
                icon = button_to_icon.get(button)
                if icon:
                    result.add(icon.lower())
    removals = overrides['remove'].get(item_name, [])
    for pattern in overrides['pattern_remove']:
        if re.match(pattern, item_name):
            removals = removals + overrides['pattern_remove'][pattern]
    return [
        x.replace('&apos;', "'")
        for x in sorted(result)
        if os.path.splitext(os.path.basename(x))[0] not in removals
    ]


def main():
    with open('workspace.json', 'r') as fp:
        config = json.load(fp)
    game_data = os.path.join(config['mod_files'], 'Mods/ArchipelagoPlayer.SC2Mod/Base.SC2Data/GameData')
    liberty_game_data = config.get('liberty_game_data')

    with open('data/overrides.json', 'r') as fp:
        overrides: dict = json.load(fp)

    item_data = get_item_data()
    item_numbers = get_item_numbers(item_data)
    upgrade_to_icon = parse_upgrade_data(os.path.join(game_data, 'UpgradeData.xml'))
    button_to_icon = parse_button_data(os.path.join(game_data, 'ButtonData.xml'))
    if liberty_game_data:
        vanilla_button_icons = parse_button_data(os.path.join(liberty_game_data, 'ButtonData.xml'))
        button_to_icon.update(vanilla_button_icons)
    id_to_unlocks = parse_galaxy_file(os.path.join(config['mod_files'], 'Mods/ArchipelagoTriggers.SC2Mod/Base.SC2Data/LibABFE498B.galaxy'))
    unit_to_ability, requirement_to_ability_button, requirement_to_ability = parse_abil_data(os.path.join(game_data, 'AbilData.xml'))
    ability_to_button, requirement_to_button = parse_unit_data(os.path.join(game_data, 'UnitData.xml'))
    upgrade_to_requirement = parse_combined_requirement_data(os.path.join(game_data, 'RequirementData.xml'), os.path.join(game_data, 'RequirementNodeData.xml'))
    validator_to_icon = parse_behaviour_data(os.path.join(game_data, 'BehaviorData.xml'))
    requirement_to_validator = parse_validator_data(os.path.join(game_data, 'ValidatorData.xml'))

    for req, buttons in requirement_to_ability_button.items():
        requirement_to_button.setdefault(req, set()).update(buttons)
    upgrade_to_icon = {key: value for key, value in upgrade_to_icon.items() if value is not None}
    button_to_icon = {key: value for key, value in button_to_icon.items() if value is not None}
    kwargs = {
        'item_numbers': item_numbers,
        'id_to_unlocks': id_to_unlocks,
        'unit_to_ability': unit_to_ability,
        'ability_to_button': ability_to_button,
        'button_to_icon': button_to_icon,
        'upgrade_to_icon': upgrade_to_icon,
        'requirement_to_button': requirement_to_button,
        'requirement_to_ability': requirement_to_ability,
        'upgrade_to_requirement': upgrade_to_requirement,
        'requirement_to_validator': requirement_to_validator,
        'validator_to_icon': validator_to_icon,
        'overrides': overrides,
    }

    found = 0
    locations = {}
    icon_paths = resolve_item_icon('Burrow Charge (Ultralisk)', **kwargs)
    for item_name in item_numbers:
        icon_paths = resolve_item_icon(item_name, **kwargs)
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
    
