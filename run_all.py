
import json
import subprocess
import os

import clean_icons
import convert
from generate import itemlist, itemgroups, missiongroups
import parse_icon_data
from filepaths import Paths

if __name__ == '__main__':
    with open('workspace.json', 'r') as fp:
        workspace = json.load(fp)
    FAST = True
    paths = Paths()
    paths.icon_paths = 'data/beta_icon_paths.json'
    paths.icon_manifest = 'data/beta_icon_manifest.json'
    paths.item_data = 'data/beta_item_data.json'
    paths.items_html = 'betaitems.html'

    current_dir = os.path.dirname(__file__)
    env = os.environ
    env['PYTHONPATH'] = workspace['ap_files'] + ';' + current_dir
    if FAST:
        return_code = subprocess.call(['python', '-m', 'scripts.clean'], env=env, cwd=workspace['ap_files'])
        assert not return_code
    return_code = subprocess.call(['python', '-m', 'scripts.export_item_data', paths.item_data, paths.item_groups], env=env)
    assert not return_code
    return_code = subprocess.call(['python', '-m', 'scripts.export_mission_data'], env=env)
    assert not return_code
    if FAST:
        return_code = subprocess.call(['python', '-m', 'scripts.clean', 'r'], env=env, cwd=workspace['ap_files'])
        assert not return_code

    parse_icon_data.main(paths)
    if not FAST: clean_icons.main()
    convert.main(paths, fast=FAST)
    itemlist.main(paths)
    missiongroups.main(paths)
    itemgroups.main(paths)
