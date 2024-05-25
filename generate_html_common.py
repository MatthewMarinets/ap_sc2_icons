"""
Common utilities for generating HTML documents.
"""

from typing import Iterable, TYPE_CHECKING, Callable, Optional
import inspect

if TYPE_CHECKING:
    import io


def brief_name(item_name: str) -> str:
    return item_name.strip().replace('/', '-').replace('(', '').replace(')', '').replace(' ', '-')


def write_table_of_contents(fp: 'io.FileIO', heading_names: Iterable[str], sort_func: Optional[Callable] = None) -> None:
    fp.write(inspect.cleandoc("""
    <div id="toc">
    <h2 id="toc-title">Table of Contents</h2>
    <ol>
    """))
    # Defeating file search with a strategy of putting invisible characters between every visible character.
    # Based on this github library:
    # https://github.com/seangransee/Disable-CTRL-F-jQuery-plugin/blob/master/disableFind.js
    spacer = "<i>=</i>"
    for heading_name in sorted(heading_names, key=sort_func):
        fp.write(f'<li><a href="#{brief_name(heading_name)}">{spacer.join(heading_name)}</a></li>\n')
        # alternate strategy -- replace each character with a look-alike
        # fp.write(f'<li><a class="no-select" href="#{brief_name(item_name)}">{confusable_hash(item_name)}</a></li>\n')
    fp.write('</ol></div>\n')


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
