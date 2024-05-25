
import json
import subprocess
import os

import clean_icons
import convert
import generate_html, generate_itemgroups_html
import parse_icon_data

if __name__ == '__main__':
    with open('workspace.json', 'r') as fp:
        workspace = json.load(fp)
    env = os.environ
    env['PYTHONPATH'] = workspace['ap_files']
    return_code = subprocess.call(['python', '-m', 'scripts.export_item_data'], env=env)
    assert not return_code

    FAST = True
    parse_icon_data.main()
    if not FAST: clean_icons.main()
    convert.main(FAST)
    generate_html.main()
    generate_itemgroups_html.main()
