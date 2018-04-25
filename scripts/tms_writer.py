# -*- coding: utf-8 -*-

import os
import sys
import getopt
from textwrap import dedent
from forge.lib.tiler import TilerManager
from forge.lib.helpers import error


def usage():
    print(dedent('''\
        Usage: venv/bin/python scripts/tms_writer.py
                  [-d database.cfg|--database=database.cfg]
                  [-c tms.cfg|--config=tms.cfg]
                  <command>

        Commands:
            create:            create the tiles and write them to S3
            metadata:          create the metadata file (layer.json)
            stats:             provides a report containing the stats
                               for a given TMS config
            statsnodb:         provides a short report containing the stats
                               for a given TMS config
    '''))


def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'c:', ['config='])
    except getopt.GetoptError as err:
        error(str(err), 2, usage=usage)

    dbConfigFile = 'configs/terrain/database.cfg'
    tmsConfigFile = 'configs/terrain/tms.cfg'
    for o, a in opts:
        if o in ('-d', '--database'):
            dbConfigFile = a
        elif o in ('-c', '--config'):
            tmsConfigFile = a

    if not os.path.exists(dbConfigFile) and os.path.exists(tmsConfigFile):
        error('config file(s) does/do not exist(s)', 1, usage=usage)

    if len(args) < 1:
        error('you must specify a command', 3, usage=usage)
    tiler = TilerManager(dbConfigFile, tmsConfigFile)

    command = args[0]
    if command == 'create':
        tiler.create()
    elif command == 'metadata':
        tiler.metadata()
    elif command == 'stats':
        tiler.stats()
    elif command == 'statsnodb':
        tiler.statsNoDb()
    # aws queue specific functions
    elif command == 'createqueue':
        tiler.createQueue()
    elif command == 'createtiles':
        tiler.createTiles()
    elif command == 'deletequeue':
        tiler.deleteQueue()
    elif command == 'queuestats':
        tiler.queueStats()
    else:
        error("unknown command '%(command)s'" % {
            'command': command}, 4, usage=usage
        )


if __name__ == '__main__':
    main()
