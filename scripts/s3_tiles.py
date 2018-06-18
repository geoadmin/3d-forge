# -*- coding: utf-8 -*-

import sys
import getopt
from textwrap import dedent
from forge.configs import tmsConfig
from forge.lib.helpers import error
from forge.lib.boto_conn import S3Keys


# One might want to provide an extent also later on
def usage():
    print(dedent('''\
        Usage: venv/bin/python scripts/s3_tiles.py
               [-p <prefix>|--prefix=<prefix>] <command>')

        Commands:
            delete:             delete all keys (tiles)
            list:               list all keys (tiles)
            count:              count all keys (tiles)
    '''))


def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'p:', ['p='])
    except getopt.GetoptError as err:
        error(str(err), 2, usage=usage)

    prefix = None
    for o, a in opts:
        if o in ('-p', '--prefix'):
            prefix = a

    if len(args) < 1:
        error('you must specify a command', 3, usage=usage)

    bucketBasePath = tmsConfig.get('General', 'bucketpath')
    s3Keys = S3Keys(prefix, bucketBasePath)

    command = args[0]
    if command == 'delete':
        s3Keys.delete()
    elif command == 'list':
        s3Keys.listKeys()
    elif command == 'count':
        s3Keys.count()
    else:
        error("unknown command '%(command)s'" % {'command': command}, 4, usage=usage)


if __name__ == '__main__':
    main()
