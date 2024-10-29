#!/usr/bin/env python

import sys

DATABASE_URL = ''

def get_connection(args):
    try:
        DATABASE_URL.connect()
    except Exception as ex:
        print(ex, file=sys.stderr)
        raise
