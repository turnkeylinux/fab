# Copyright (c) TurnKey Linux - http://www.turnkeylinux.org
#
# This file is part of Fab
#
# Fab is free software; you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by the
# Free Software Foundation; either version 3 of the License, or (at your
# option) any later version.

import os
import sys
import getopt

# patch gnu_getopt to support "-" as a argument (like getopt does)
def gnu_getopt(args, options, long_options=[]):
    def list_replace(l, a, b):
        for i in range(len(l)):
            if l[i] == a:
                l[i] = b

    list_replace(args, "-", "__stdin__")

    opts, args = getopt.gnu_getopt(args, options, long_options)

    list_replace(args, "__stdin__", "-")
    return opts, args
    
def mkdir(path):
    path = str(path)
    if not os.path.exists(path):
        os.makedirs(path)

## cli common
def fatal(s):
    print >> sys.stderr, "error: " + str(s)
    sys.exit(1)

def warn(s):
    print >> sys.stderr, "warning: " + str(s)
