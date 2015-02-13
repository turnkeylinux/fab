#!/usr/bin/python
# Copyright (c) TurnKey GNU/Linux - http://www.turnkeylinux.org
#
# This file is part of Fab
#
# Fab is free software; you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by the
# Free Software Foundation; either version 3 of the License, or (at your
# option) any later version.

"""
Prints package information

Arguments:
  <packages> := ( - | path/to/plan | path/to/spec | package[=version] ) ...
                If a version isn't specified, the newest version is implied.

Options:
  -p --pool=PATH    set pool path (default: $FAB_POOL_PATH)

  (Also accepts fab-cpp options to effect plan preprocessing)
"""

import os
from os.path import *

import sys
import getopt

import help
import cpp
from plan import Plan
from common import gnu_getopt

@help.usage(__doc__)
def usage():
    print >> sys.stderr, "Syntax: %s [-options] <packages>" % sys.argv[0]

def generate_index(dctrls):
    # field ordering according to DPM - Chap5: Control files and their fields
    fields = ('Package', 'Essential', 'Priority', 'Section', 'Installed-Size', 
              'Maintainer', 'Original-Maintainer', 'Uploaders', 'Changed-By', 
              'Architecture', 'Source', 'Version',
              'Depends', 'Pre-Depends', 'Recommends', 'Suggests', 'Conflicts', 
              'Provides', 'Replaces', 'Enhances',
              'Filename', 'Description')

    index = []
    for dep, control in dctrls.items():
        for field in fields:
            if field not in control.keys():
                continue
            index.append(field + ": " + control[field])

        index.append('')

    return "\n".join(index)

def main():
    cpp_opts, args = cpp.getopt(sys.argv[1:])
    try:
        opts, args = gnu_getopt(args, 'p:', ['pool='])
    except getopt.GetoptError, e:
        usage(e)

    if not args:
        usage()

    pool_path = None

    for opt, val in opts:
        if opt in ('-p', '--pool'):
            pool_path = val

    if pool_path is None:
        pool_path = os.environ.get('FAB_POOL_PATH')

    plan = Plan(pool_path=pool_path)
    for arg in args:
        if arg == "-" or exists(arg):
            plan |= Plan.init_from_file(arg, cpp_opts, pool_path)
        else:
            plan.add(arg)

    dctrls = plan.dctrls()
    print generate_index(dctrls)


if __name__=="__main__":
    main()

