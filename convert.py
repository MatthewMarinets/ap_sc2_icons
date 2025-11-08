"""
Convert .dds icons to .png under the `icons/` folder using magick.
"""

from typing import *
import json
from pathlib import Path
import os
import subprocess

from filepaths import Paths

ORIGINAL_DIR = 'icons/original'
BLIZZARD_DIR = 'icons/blizzard'


def main(paths: Paths, fast: bool = True) -> None:
    verbose = False
    extras = {
        '_terran': ['ui_glues_help_armyicon_terran.dds'],
        '_protoss': ['ui_glues_help_armyicon_protoss.dds'],
        '_zerg': ['ui_glues_help_armyicon_zerg.dds'],
    }
    with open(paths.workspace, 'r') as fp:
        config: dict[str, str] = json.load(fp)
    with open(paths.icon_paths, 'r') as fp:
        location_info: dict[str, dict] = json.load(fp)
    dds_dir = config['dds_files']
    mod_dir = config['mod_files']

    failures = 0
    successes = 0
    skipped = 0
    no_information = 0
    parsed_locations: dict[str, list[str]] = location_info['locations']
    parsed_locations.update(extras)
    for key in parsed_locations:
        parsed_locations[key] = [x.replace('\\', '/') for x in parsed_locations[key]]
    info = {}
    items = sorted(parsed_locations)
    if not os.path.exists(ORIGINAL_DIR):
        os.makedirs(ORIGINAL_DIR)
    if not os.path.exists(BLIZZARD_DIR):
        os.makedirs(BLIZZARD_DIR)
    converted: set[str] = set()
    for item_number, item in enumerate(items):
        if item_number % 50 == 0:
            print(f'{item_number} / {len(items)}')
        locations = parsed_locations[item]
        if not locations:
            no_information += 1
            continue
        filenames = [os.path.basename(x) for x in locations]
        stems = [os.path.splitext(x)[0] for x in filenames]
        for location, filename, stem in zip(locations, filenames, stems):
            if location.lower().startswith('ap'):
                target_dir = ORIGINAL_DIR
                assets_dir = f'{mod_dir}/Mods/ArchipelagoPlayer.SC2Mod/Base.SC2Assets'
                source_path = f'{assets_dir}/{location}'
                source_cased_path = list(Path(assets_dir).glob(location, case_sensitive=False))
            else:
                target_dir = BLIZZARD_DIR
                source_path = os.path.join(dds_dir, filename)
                source_cased_path = list(Path(dds_dir).glob(filename, case_sensitive=False))
            if not source_cased_path:
                print(f'Failure: {source_path} does not exist')
                failures += 1
                continue
            target_path = f'{target_dir}/{stem}.png'
            if target_path in converted or (fast and os.path.isfile(target_path)):
                skipped += 1
                if verbose: print(f'Skipping {target_path} as it is already converted')
            else:
                retval = subprocess.call(f'convert "{source_cased_path[0]}" -define png:exclude-chunk=date,time {target_path}', shell=True)
                if retval:
                    failures += 1
                    print(f'magick returned non-zero value {retval} trying to convert {source_path}')
                    continue
                successes += 1
                converted.add(target_path)
            info.setdefault(item, []).append(target_path)
    with open(paths.icon_manifest, 'w') as fp:
        json.dump(info, fp, indent=1)
    print(f'Converted: {successes} | Skipped (duplicate): {skipped} | Failed: {failures} | No path: {no_information} | Items: {len(items)}')


if __name__ == '__main__':
    main(Paths())
