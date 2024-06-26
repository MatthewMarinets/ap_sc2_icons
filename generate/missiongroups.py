"""
Generate an HTML for displaying mission groups.
"""

from typing import *
import inspect
import json

from filepaths import Paths
from generate.html_common import brief_name, write_table_of_contents, write_topbar_nav

if TYPE_CHECKING:
    import io


def write_start(fp: 'io.FileIO') -> None:
    fp.write(inspect.cleandoc("""
    <!doctype html>
    <html>
    <head>
        <title>APSC2 Mission Groups</title>
        <meta name="description" content="Explanation of Archipelago sc2 mission groups"/>
        <meta name="keywords" content="Archipelago Starcraft 2"/>
        <link rel="stylesheet" href="styles/common.css"/>
        <link rel="icon" type="image/png" href="favicon.png"/>
        <style>
        .missiongroup-container {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(15rem, 1fr));
        }
        </style>
    </head>
    <body style="background-color: black; color: #ebb">
        <div id="main-content">
    """))


def write_title(fp: 'io.FileIO') -> None:
    fp.write('<h1>Mission Groups</h1>')
    fp.write('<p style="text-align: center">A list of mission groups and what they expand to.<br>Note this is beta content.</p>')


def write_group(
    fp: 'io.FileIO',
    group_name: str,
    group_contents: Iterable[str],
    mission_data: dict[str, dict[str, str]],
    icons: dict[str, list[str]]
) -> None:
    DEFAULT_IMAGE = 'favicon.png'
    fp.write(inspect.cleandoc(f"""
    <div id="{group_name}">
        <a id="{brief_name(group_name)}"></a><a href="#{brief_name(group_name)}" class="item-title"><h2>{group_name}</h2></a>
        <div class="missiongroup-container">
    """))
    items = sorted(group_contents)
    for item in items:
        faction = mission_data.get(item, {}).get('faction')
        if faction == 'Terran':
            icon = icons['_terran'][0]
        elif faction == 'Zerg':
            icon = icons['_zerg'][0]
        elif faction == 'Protoss':
            icon = icons['_protoss'][0]
        else:
            icon = DEFAULT_IMAGE
        fp.write(
            f'<div class="group-list-item">'
            f'<img class="list-item-icon" src="{icon}">'
            f'<p class="list-item-label">{item}</p>'
            f'</div>'
        )
    fp.write('</div></div>')


def write_end(fp: 'io.FileIO') -> None:
    fp.write(inspect.cleandoc("""
    </div>
    </body>
    </html>
    """))


def main(paths: Paths) -> None:
    with open(paths.mission_data, 'r') as fp:
        mission_data: dict[str, dict[str, str]] = json.load(fp)
    with open(paths.mission_groups, 'r') as fp:
        mission_groups: dict[str, list[str]] = json.load(fp)
    with open(paths.icon_manifest, 'r') as fp:
        icons: dict[str, list[str]] = json.load(fp)
    with open(paths.mission_groups_html, 'w', encoding='utf-8') as fp:
        write_start(fp)
        write_topbar_nav(fp, paths)
        write_table_of_contents(fp, mission_groups)
        write_title(fp)
        for group_name, group_contents in mission_groups.items():
            write_group(fp, group_name, group_contents, mission_data, icons)
        write_end(fp)


if __name__ == '__main__':
    main(Paths())
