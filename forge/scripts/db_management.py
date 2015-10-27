# -*- coding: utf-8 -*-

import sys
import getopt
from textwrap import dedent
from forge.db import DB
from forge.lib.helpers import error


def usage():
    print(dedent('''\
        Usage: venv/bin/python forge/script/db_management.py
               [-c database.cfg|--config=database.cfg] <command>')

        Commands:
            console:            enter interactive psql console
            create:             create the DB and users
            createuser:         create the user only
            createdb:           create the DB only
            setupfunctions:     setup custom sql functions
            populate:           imports shapefiles
            populatelakes:      imports lakes shapefile
            dropuser:           drop the user only
            dropdb:             drop the db only
            destroy:            destroy the database and users
    '''))


def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'c:', ['config='])
    except getopt.GetoptError as err:
        error(str(err), 2, usage=usage)

    dbConfigFile = 'configs/terrain/database.cfg'
    for o, a in opts:
        if o in ('-c', '--config'):
            dbConfigFile = a

    if len(args) < 1:
        error('you must specify a command', 3, usage=usage)

    db = DB(dbConfigFile)

    command = args[0]
    if command == 'console':
        db.console()
    elif command == 'create':
        db.create()
    elif command == 'createuser':
        db.createUser()
    elif command == 'createdb':
        db.createDB()
    elif command == 'setupfunctions':
        db.setupFunctions()
    elif command == 'populate':
        db.populate()
    elif command == 'populatelakes':
        db.populateLakes()
    elif command == 'dropuser':
        db.dropUser()
    elif command == 'dropdb':
        db.dropDatabase()
    elif command == 'destroy':
        db.destroy()
    else:
        error("unknown command '%(command)s'" % {'command': command}, 4, usage=usage)

if __name__ == '__main__':
    main()
