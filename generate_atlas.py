import subprocess
import os
import glob
import json
import shutil

MAGICK = 'magick'
if not shutil.which(MAGICK):
    with open('workspace.json', 'r') as fp:
        workspace = json.load(fp)
    # Note(mm): This script requires magick v7
    # Note(mm): On Linux, it can be downloaded from https://imagemagick.org/script/download.php
    MAGICK = workspace['magick']


def create_texture_atlas(
    icon_manifest_path: str, atlas_file: str, metadata_out: str, clean_build: bool = False
) -> None:
    with open(icon_manifest_path, 'r') as fp:
        icon_manifest: dict[str, list[str]] = json.load(fp)
    icons = set(inner for x in icon_manifest.values() for inner in x)
    if os.path.isdir('build') and clean_build:
        shutil.rmtree('build')
    os.makedirs('build', exist_ok=True)

    num_icons = len(icons)
    print(f"Converting {num_icons} icons")

    for index, icon in enumerate(icons, start=1):
        target_file = f'build/{os.path.basename(icon)}'
        # if os.path.basename(icon) == 'btn-ability-mengsk-trooper-advancedconstruction.png':
        #     # The things I do for backwards compatibility...
        #     target_file = f'build/btn-advanced-construction.png'
        if not os.path.isfile(target_file):
            subprocess.call([MAGICK, icon, '-resize', r'76x76\!', target_file])
        stats = subprocess.run([MAGICK, 'identify', target_file], stdout=subprocess.PIPE)
        parts = stats.stdout.decode('utf-8').split(' ', 3)
        assert parts[2] == '76x76', f"icon {icon} is {parts[2]}"
        if index % (num_icons // 10) == 0:
            print(f"Converting: {index}/{num_icons}")
    for icon in icons:
        assert os.path.isfile(icon)
    if os.path.isfile(atlas_file):
        os.unlink(atlas_file)
    subprocess.call([MAGICK, 'montage', '-mode', 'concatenate', '-tile', '1x', '-background', 'black', 'build/*.png', atlas_file])
    image_order = sorted([os.path.basename(x) for x in glob.glob('build/*.png')])
    metadata = {
        'num_images': len(image_order),
        'order': {image: index for index, image in enumerate(image_order)},
    }
    with open(metadata_out, 'w') as fp:
        json.dump(metadata, fp)


if __name__ == '__main__':
    create_texture_atlas(
        # 'data/beta_icon_manifest.json',
        'data/icon_manifest.json',
        'icons/atlas.v4.0.0.png',
        'data/atlas.v4.0.0.json',
        # clean_build=True,
    )
