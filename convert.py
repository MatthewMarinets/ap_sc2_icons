"""
Convert .dds icons to .png under the `icons/` folder using magick.
"""

from typing import *
import json
import os
import subprocess

if __name__ == '__main__':
    with open('workspace.json', 'r') as fp:
        config: dict[str, str] = json.load(fp)
    with open('data/locations.json', 'r') as fp:
        location_info: dict[str, dict] = json.load(fp)
    dds_dir = config['dds_files']
    mod_dir = config['mod_files']
    failures = 0
    locations = location_info['locations']
    num_images = location_info["meta"]["located"]
    for item, location in locations.items():
        if not location:
            continue
        filename = os.path.basename(location)
        stem = os.path.splitext(filename)[0]
        if location.startswith('AP'):
            target_dir = 'icons/original'
            source_path = os.path.join(mod_dir, 'Mods/ArchipelagoPlayer.SC2Mod/Base.SC2Assets', location)
        else:
            target_dir = 'icons/blizzard'
            source_path = os.path.join(dds_dir, filename)
        if not os.path.exists(source_path):
            print(f'Failure: {source_path} does not exist')
            failures += 1
            continue
        retval = subprocess.call(f'magick convert "{source_path}" {target_dir}/{stem}.png', shell=True)
        if retval:
            failures += 1
            print(f'magick returned non-zero value {retval} trying to convert {source_path}')
    print(f'Converted {num_images - failures} images | Encountered {failures} errors | Total {num_images} items')
