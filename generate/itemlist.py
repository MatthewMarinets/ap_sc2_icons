
from typing import *
import json
import io
import os
import inspect

from filepaths import Paths
from generate.html_common import brief_name, write_table_of_contents, write_topbar_nav


def write_start(fp: io.FileIO) -> None:
    fp.write(inspect.cleandoc("""
    <!doctype html>
    <html>
    <head>
        <title>Starcraft 2 Icon Repository</title>
        <meta name="description" content="A repository of Starcraft 2 icons used in Archipelago"/>
        <meta name="keywords" content="Archipelago Starcraft 2"/>
        <link rel="stylesheet" href="styles/common.css"/>
        <link rel="icon" type="image/png" href="favicon.png"/>
        <style>
        img {
            display: inline-block;
            margin: auto;
            max-width: 96px;
            height: auto;
        }
        </style>
    </head>
    <body style="background-color: black; color: #ebb">
        <div id="main-content">
    """))


def write_title(fp: 'io.FileIO') -> None:
    fp.write('<h1>Items</h1>')
    fp.write('<p style="text-align: center">A list of items with icons and descriptions.<br>Note this is beta content.</p>')


def write_item(fp: io.FileIO, item_name: str, item_info: str, icon_locations: list[str]) -> None:
    fp.write(inspect.cleandoc(f"""
    <div id="{item_name}">
        <a id="{brief_name(item_name)}"></a><a href="#{brief_name(item_name)}" class="item-title"><h2>{item_name}</h2></a>
        <div class="image-container">
    """))
    icon_locations = sorted(icon_locations, key=os.path.basename)
    if not icon_locations:
        fp.write('<p class="error">Icon unavailable</p>')
    locations_list_items = ''
    for location in icon_locations:
        fp.write(f'<img src="{location}"/>')
    #     locations_list_items += f'<li>Icon path: <code>{location}</code></li>'
    fp.write(inspect.cleandoc(f"""
        </div>
        <ul>
        <li>Faction: {item_info["race"]}</li>
        <li>Classification: {item_info["classification"]}</li>
        {f'<li>Description: {item_info["description"]}</li>' if item_info["description"] else ''}
        {f'<li>Parent: {item_info["parent_item"]}</li>' if item_info["parent_item"] else ''}
        {locations_list_items}
        </ul>
    </div>
    """))


def write_end(fp: io.FileIO) -> None:
    fp.write(inspect.cleandoc("""
        </div>
    </body>
    </html>
    """))


def item_sort_func(item_name: str) -> tuple:
    if ' (' in item_name:
        parts = item_name.split(' (')
        assert len(parts) == 2, f'item "{item_name}" has multiple parens'
        if parts[1] in ('Zerg)', 'Terran)', 'Protoss)', 'Terran/Zerg)'):
            return ('(' + parts[1], parts[0])
        return (parts[1], parts[0])
    return ('', item_name)


def main(paths: Paths) -> None:
    with open(paths.item_data, 'r') as fp:
        item_data = json.load(fp)
    with open(paths.icon_manifest, 'r') as fp:
        icon_manifest = json.load(fp)
    with open(paths.items_html, 'w', encoding='utf-8') as fp:
        write_start(fp)
        write_topbar_nav(fp, paths)
        write_table_of_contents(fp, item_data, sort_func=item_sort_func)
        write_title(fp)
        for item in item_data:
            write_item(fp, item, item_data[item], icon_manifest.get(item, []))
        write_end(fp)

if __name__ == '__main__':
    main(Paths())
