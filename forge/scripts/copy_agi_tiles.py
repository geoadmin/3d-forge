# -*- coding: utf-8 -*-

from textwrap import dedent
from forge.configs import tmsConfig
from forge.lib.utils import copyAGITiles


# One might want to provide an extent also later on
def usage():
    print(dedent('''\
        Usage: venv/bin/python forge/script/copy_agi_tiles.py')
    '''))


def main():
    zooms = range(0, 8)
    bounds = [-180, -90, 180, 90]
    bucketBasePath = tmsConfig.get('General', 'bucketpath')
    copyAGITiles(zooms, bounds, bucketBasePath)


if __name__ == '__main__':
    main()
