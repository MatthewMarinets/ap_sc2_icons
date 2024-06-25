
import json
import subprocess
import os

import clean_icons
import convert
import generate_html, generate_itemgroups_html, generate_missiongroups_html
import parse_icon_data
from filepaths import Paths

if __name__ == '__main__':
    with open('workspace.json', 'r') as fp:
        workspace = json.load(fp)
    paths = Paths()
    paths.icon_paths = 'data/beta_icon_paths.json'
    paths.icon_manifest = 'data/icon_manifest.json'
    paths.item_data = 'data/beta_item_data.json'

    env = os.environ
    env['PYTHONPATH'] = workspace['ap_files']
    return_code = subprocess.call(['python', '-m', 'scripts.export_item_data', paths.item_data, paths.item_groups], env=env)
    assert not return_code
    return_code = subprocess.call(['python', '-m', 'scripts.export_mission_data'], env=env)
    assert not return_code

    FAST = True
    parse_icon_data.main(paths)
    if not FAST: clean_icons.main()
    convert.main(paths, fast=FAST)
    generate_html.main(paths)
    generate_missiongroups_html.main(paths)
    generate_itemgroups_html.main(paths)
