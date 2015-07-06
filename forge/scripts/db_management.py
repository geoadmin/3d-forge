# -*- coding: utf-8 -*-

import sys
import getopt
from textwrap import dedent
from forge import DB


def usage():
    print(dedent('''\
        Usage: ./geodb.py [-c database.cfg|--config=database.cfg] <command>')

        Commands:
            create:             create the database. Fails if already exist.
            destroy:            destroy the database.
    '''))


def error(msg, exitCode=1):
    print('Error: %(msg)s.' % {'msg': msg})
    print('')
    usage()
    sys.exit(exitCode)


def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'c:', ['config='])
    except getopt.GetoptError as err:
        error(str(err), 2)

    config = 'database.cfg'
    for o, a in opts:
        if o in ('-c', '--config'):
            config = a

    if len(args) < 1:
        error('you must specify a command', 3)

    db = DB(config)

    command = args[0]
    if command == 'create':
        db.create()
    elif command == 'destroy':
        db.destroy()
    else:
        error("unknown command '%(command)s'" % {'command': command}, 4)

if __name__ == '__main__':
    main()
