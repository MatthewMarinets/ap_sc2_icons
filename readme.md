# Starcraft 2 icon data
This is a repository of Starcraft 2 button icons for use with Archipelago displays and trackers.

## Licensing
Icons under the `icons/blizzard` directory are property of Blizzard Entertainment. They are licensed under the Blizzard license under `license/Blizzard.LICENSE` They are extracted from the gamefiles and converted from .dds format to .png format.

Icons under `icons/original` are fan creations, provided by various contributors and licensed under MIT. Their licenses may be found in the `license/` folder.

## Processing
Icons are extracted from the sc2 game files using a CASC editor such as Zezula's CascView. These icons are in .dds format, and are converted to .png using open-source tool `magick`.

## Parsing
`parse_icon_data.py` can be used to parse

## Script configuration
The scripts use path information pulled from a workspace.json file in the root of the directory tree. This information is user-specific, and is thus not checked in.
