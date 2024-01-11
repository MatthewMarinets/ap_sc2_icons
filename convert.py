"""
Convert .dds icons to .png under the `icons/` folder using magick.
"""

from typing import *
import json
import os
import subprocess

ORIGINAL_DIR = 'icons/original'
BLIZZARD_DIR = 'icons/blizzard'

if __name__ == '__main__':
    verbose = False
    with open('workspace.json', 'r') as fp:
        config: dict[str, str] = json.load(fp)
    with open('data/locations.json', 'r') as fp:
        location_info: dict[str, dict] = json.load(fp)
    dds_dir = config['dds_files']
    mod_dir = config['mod_files']
    failures = 0
    successes = 0
    skipped = 0
    no_information = 0
    locations = location_info['locations']
    num_images = location_info["meta"]["located"]
    info = {}
    items = sorted(locations)
    if not os.path.exists(ORIGINAL_DIR):
        os.makedirs(ORIGINAL_DIR)
    if not os.path.exists(BLIZZARD_DIR):
        os.makedirs(BLIZZARD_DIR)

    for item in items:
        location = locations[item]
        if not location:
            no_information += 1
            continue
        filename = os.path.basename(location)
        stem = os.path.splitext(filename)[0]
        if location.startswith('AP'):
            target_dir = ORIGINAL_DIR
            source_path = os.path.join(mod_dir, 'Mods/ArchipelagoPlayer.SC2Mod/Base.SC2Assets', location)
        else:
            target_dir = BLIZZARD_DIR
            source_path = os.path.join(dds_dir, filename)
        if not os.path.exists(source_path):
            print(f'Failure: {source_path} does not exist')
            failures += 1
            continue
        target_path = f'{target_dir}/{stem}.png'
        if os.path.exists(target_path):
            if verbose: print(f'Skipping {target_path} as it already exists')
            info[item] = target_path
            skipped += 1
            continue
        retval = subprocess.call(f'magick convert "{source_path}" -define png:exclude-chunk=date,time {target_path}', shell=True)
        if retval:
            failures += 1
            print(f'magick returned non-zero value {retval} trying to convert {source_path}')
            continue
        successes += 1
        info[item] = target_path
    with open('data/icon_manifest.json', 'w') as fp:
        json.dump(info, fp, indent=1)
    print(f'Converted: {successes} | Skipped: {skipped} | Failed: {failures} | No path: {no_information} | Total: {len(items)}')
