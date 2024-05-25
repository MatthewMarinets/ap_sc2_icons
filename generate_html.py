
from typing import *
import json
import io
import inspect

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
            max-width: 100%;
            height: auto;
        }
        </style>
    </head>
    <body style="background-color: black; color: #ebb">
        <div id="main-content">
    """))

def brief_name(item_name: str) -> str:
    return item_name.strip().replace('/', '-').replace('(', '').replace(')', '').replace(' ', '-')


def confusable_hash_char(char: str) -> str:
    integer = ord(char)
    if (integer >= ord('a') and integer <= ord('z')):
        # Use Mathematical sans-serif normal characters
        return chr(0x1D5BA + integer - ord('a'))
    if (integer >= ord('A') and integer <= ord('Z')):
        # Use Mathematical sans-serif normal characters
        return chr(0x1D5A0 + integer - ord('A'))
    if (integer >= ord('0') and integer <= ord('9')):
        return chr(0x1D7E2 + integer - ord('0'))
    return char

def confusable_hash(string: str) -> str:
    """Replaces all characters in a string with look-alike characters to prevent search from picking them up"""
    return ''.join(confusable_hash_char(c) for c in string)


def write_table_of_contents(fp: io.FileIO, item_names: Iterable[str]) -> None:
    fp.write(inspect.cleandoc("""
    <div id="toc">
    <h2 id="toc-title">Table of Contents</h2>
    <ol>
    """))
    # Defeating file search with a strategy of putting invisible characters between every visible character.
    # Based on this github library:
    # https://github.com/seangransee/Disable-CTRL-F-jQuery-plugin/blob/master/disableFind.js
    spacer = "<i>=</i>"
    for item_name in sorted(item_names, key=lambda x: tuple(reversed(x.split(' ('))) if ' (' in x else ('', x)):
        fp.write(f'<li><a href="#{brief_name(item_name)}">{spacer.join(item_name)}</a></li>\n')
        # alternate strategy -- replace each character with a look-alike
        # fp.write(f'<li><a class="no-select" href="#{brief_name(item_name)}">{confusable_hash(item_name)}</a></li>\n')
    fp.write('</ol></div>\n')

def write_item(fp: io.FileIO, item_name: str, item_info: str, icon_locations: list[str]) -> None:
    fp.write(inspect.cleandoc(f"""
    <div id="{item_name}">
        <a id="{brief_name(item_name)}"></a><a href="#{brief_name(item_name)}" class="item-title"><h2>{item_name}</h2></a>
        <div class="image-container">
    """))
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

def main() -> None:
    with open('data/item_data.json', 'r') as fp:
        item_data = json.load(fp)
    with open('data/icon_manifest.json', 'r') as fp:
        icon_manifest = json.load(fp)
    with open('index.html', 'w', encoding='utf-8') as fp:
        write_start(fp)
        write_table_of_contents(fp, item_data)
        for item in item_data:
            write_item(fp, item, item_data[item], icon_manifest.get(item, []))
        write_end(fp)

if __name__ == '__main__':
    main()
