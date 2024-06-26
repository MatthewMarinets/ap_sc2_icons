"""
Generate an HTML for displaying item groups.
"""

from typing import *
import inspect
import json

from filepaths import Paths
from generate.html_common import brief_name, write_table_of_contents

if TYPE_CHECKING:
    import io


def write_start(fp: 'io.FileIO') -> None:
    fp.write(inspect.cleandoc("""
    <!doctype html>
    <html>
    <head>
        <title>APSC2 Item Groups</title>
        <meta name="description" content="Explanation of Archipelago sc2 item groups"/>
        <meta name="keywords" content="Archipelago Starcraft 2"/>
        <link rel="stylesheet" href="styles/common.css"/>
        <link rel="icon" type="image/png" href="favicon.png"/>
        <style>
        .itemgroup-container {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(25rem, 1fr));
        }
        .list-item-label {
            color: #ebb;
        }
        </style>
    </head>
    <body style="background-color: black; color: #ebb">
        <div id="main-content">
    """))


def write_title(fp: 'io.FileIO') -> None:
    fp.write('<h1>Item Groups</h1>')
    fp.write('<p style="text-align: center">A list of item groups and what they expand to.<br>Note this is largely beta content.</p>')


def write_group(
    fp: 'io.FileIO',
    group_name: str,
    group_contents: Iterable[str],
    icon_manifest: dict[str, list[str]],
    item_page_rel_path: str
) -> None:
    DEFAULT_IMAGE = 'favicon.png'
    fp.write(inspect.cleandoc(f"""
    <div id="{group_name}">
        <a id="{brief_name(group_name)}"></a><a href="#{brief_name(group_name)}" class="item-title"><h2>{group_name}</h2></a>
        <div class="itemgroup-container">
    """))
    items = sorted(group_contents)
    for item in items:
        fp.write(
            f'<div class="group-list-item">'
            f'<img class="list-item-icon" src="{icon_manifest.get(item, [DEFAULT_IMAGE])[0]}">'
            f'<a class="list-item-label" href="{item_page_rel_path}#{brief_name(item)}">{item}'
            f'</a></div>'
        )
    fp.write('</div></div>')


def write_end(fp: 'io.FileIO') -> None:
    fp.write(inspect.cleandoc("""
    </div>
    </body>
    </html>
    """))


def main(paths: Paths) -> None:
    with open(paths.item_groups, 'r') as fp:
        item_groups: dict[str, list[str]] = json.load(fp)
    with open(paths.icon_manifest, 'r') as fp:
        icon_manifest = json.load(fp)
    item_page_rel_path = f'./{paths.items_html}'
    with open(paths.item_groups_html, 'w', encoding='utf-8') as fp:
        write_start(fp)
        write_table_of_contents(fp, item_groups)
        write_title(fp)
        for group_name, group_contents in item_groups.items():
            write_group(fp, group_name, group_contents, icon_manifest, item_page_rel_path)
        write_end(fp)


if __name__ == '__main__':
    main(Paths())
