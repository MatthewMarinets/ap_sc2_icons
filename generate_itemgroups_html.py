"""
Generate an HTML for displaying item groups.
"""

from typing import *
import inspect
import json

if TYPE_CHECKING:
    import io


ITEM_PAGE_REL_PATH = './index.html'


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
        .item-icon {
            max-width: 1.4em;
            vertical-align: middle;
        }
        .item-label {
            display: inline;
            vertical-align: middle;
        }
        a {
            color: #ebb;
        }
        </style>
    </head>
    <body style="background-color: black; color: #ebb">
        <div id="main-content">
    """))


def brief_name(item_name: str) -> str:
    return item_name.strip().replace('/', '-').replace('(', '').replace(')', '').replace(' ', '-')


def write_table_of_contents(fp: 'io.FileIO', group_names: Iterable[str]) -> None:
    fp.write(inspect.cleandoc("""
    <div id="toc">
    <h2 id="toc-title">Table of Contents</h2>
    <ol>
    """))
    # Defeating file search with a strategy of putting invisible characters between every visible character.
    # Based on this github library:
    # https://github.com/seangransee/Disable-CTRL-F-jQuery-plugin/blob/master/disableFind.js
    spacer = "<i>=</i>"
    for group_name in sorted(group_names):
        fp.write(f'<li><a href="#{brief_name(group_name)}">{spacer.join(group_name)}</a></li>\n')
        # alternate strategy -- replace each character with a look-alike
        # fp.write(f'<li><a class="no-select" href="#{brief_name(item_name)}">{confusable_hash(item_name)}</a></li>\n')
    fp.write('</ol></div>\n')


def write_title(fp: 'io.FileIO') -> None:
    fp.write('<h1>Item Groups</h1>')
    fp.write('<p style="text-align: center">A list of item groups and what they expand to.</p>')


def write_group(fp: 'io.FileIO', group_name: str, group_contents: Iterable[str], icon_manifest: dict[str, list[str]]) -> None:
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
            f'<img class="item-icon" src="{icon_manifest.get(item, [DEFAULT_IMAGE])[0]}">'
            f'<a class="item-label" href="{ITEM_PAGE_REL_PATH}#{brief_name(item)}">{item}'
            f'</a></div>'
        )
    fp.write('</div></div>')


def write_end(fp: 'io.FileIO') -> None:
    fp.write(inspect.cleandoc("""
    </div>
    </body>
    </html>
    """))


def main() -> None:
    with open('data/item_groups.json', 'r') as fp:
        item_groups: dict[str, list[str]] = json.load(fp)
    with open('data/icon_manifest.json', 'r') as fp:
        icon_manifest = json.load(fp)
    with open('itemgroups.html', 'w', encoding='utf-8') as fp:
        write_start(fp)
        write_table_of_contents(fp, item_groups)
        write_title(fp)
        for group_name, group_contents in item_groups.items():
            write_group(fp, group_name, group_contents, icon_manifest)
        write_end(fp)


if __name__ == '__main__':
    main()
