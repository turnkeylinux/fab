#!/usr/bin/python
# Copyright (c) TurnKey GNU/Linux - http://www.turnkeylinux.org
#
# This file is part of Fab
#
# Fab is free software; you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by the
# Free Software Foundation; either version 3 of the License, or (at your
# option) any later version.

"""Apply overlay on top of given path

Arguments:
  <overlay>         Path to overlay
  <path>            Path to apply overlay ontop of (ie. chroot)

Options:
  --preserve        Perserve mode,ownership and timestamps

"""

import os
import sys
import getopt

import help
import executil
from common import fatal


@help.usage(__doc__)
def usage():
    print("Syntax: %s [-options] <overlay> <path>" % sys.argv[0], file=sys.stderr)


def apply_overlay(overlay, dstpath, preserve=False):
    cmd = "cp -TdR"
    if preserve:
        cmd += " -p"

    executil.system(cmd, overlay, dstpath)


def main():
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], "", ["preserve"])
    except getopt.GetoptError as e:
        usage(e)

    if not len(args) == 2:
        usage()

    overlay = args[0]
    dstpath = args[1]

    kws = {}
    for opt, val in opts:
        kws[opt[2:]] = val

    for dir in (overlay, dstpath):
        if not os.path.isdir(dir):
            fatal("does not exist: " + dir)

    apply_overlay(overlay, dstpath, **kws)


if __name__ == "__main__":
    main()
