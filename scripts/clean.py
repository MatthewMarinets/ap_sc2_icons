#! /usr/bin/env python3
import os
import glob
import shutil

def clean(verbose: bool = True) -> None:
    shutil.rmtree('_worlds/__pycache__', ignore_errors=True)
    worlds = glob.glob('worlds/*')
    for world in worlds:
        if os.path.basename(world) in ('_sc2common', 'sc2', '__pycache__', 'alttp', 'generic'):
            continue
        if os.path.splitext(world)[1] == '.py':
            continue
        if verbose:
            print(f'Removing {world}')
        os.rename(world, world.replace('worlds', '_worlds'))

def restore(verbose: bool = True) -> None:
    worlds = glob.glob('_worlds/*')
    print("Restoring all worlds")
    for world in worlds:
        if os.path.basename(world) == '__pycache__':
            shutil.rmtree(world)
            continue
        if verbose:
            print(f'Restoring {world}')
        os.rename(world, world.replace('_worlds', 'worlds'))

if __name__ == '__main__':
    import sys
    mode = 'clean'
    for arg in sys.argv[1:]:
        if arg in ('r', 'restore'):
            mode = 'restore'
        elif arg in ('c', 'clean'):
            pass
        else:
            print(f"Unknown argument '{arg}'")
            sys.exit()
    if mode == 'clean':
        clean()
    elif mode == 'restore':
        restore()
    print('done')
