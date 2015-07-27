# -*- coding: utf-8 -*-

import sys
import getopt
from textwrap import dedent
from forge import DB
from forge.lib.helpers import error


def usage():
    print(dedent('''\
        Usage: venv/bin/python forge/script/db_management.py [-c database.cfg|--config=database.cfg] <command>')

        Commands:
            create:             create the database. Fails if already exist.
            importshp:          imports shapefiles
            destroy:            destroy the database.
    '''))


def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'c:', ['config='])
    except getopt.GetoptError as err:
        error(str(err), 2, usage=usage)

    config = 'database.cfg'
    for o, a in opts:
        if o in ('-c', '--config'):
            config = a

    if len(args) < 1:
        error('you must specify a command', 3, usage=usage)

    db = DB(config)

    command = args[0]
    if command == 'create':
        db.create()
    elif command == 'importshp':
        db.importshp()
    elif command == 'destroy':
        db.destroy()
    else:
        error("unknown command '%(command)s'" % {'command': command}, 4, usage=usage)

if __name__ == '__main__':
    main()
