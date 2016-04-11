#!/usr/bin/python
# Copyright (c) TurnKey GNU/Linux - http://www.turnkeylinux.org
#
# This file is part of Fab
#
# Fab is free software; you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by the
# Free Software Foundation; either version 3 of the License, or (at your
# option) any later version.

"""Apply patch on top of given path

Arguments:
  <patch>           Path to patch
  <path>            Path to apply patch ontop of (ie. build/root.patched)

Patches:            Patches should be in unified context produced by diff -u
                    Filenames must be in absolute path format from the root
                    Patches may be uncompressed, compressed with gzip (.gz),
                    or bzip2 (.bz2)

"""

import os
import sys
import getopt

import help
import executil
from common import fatal

@help.usage(__doc__)
def usage():
    print >> sys.stderr, "Syntax: %s <patch> <path>" % sys.argv[0]

def apply_patch(patch, dstpath):
    if patch.endswith('.gz'):
        cmd = "zcat"
    elif patch.endswith('.bz2'):
        cmd = "bzcat"
    else:
        cmd = "cat"
    """
    patch options
       -N --forward     ignore if patch has already been applied
       -b --backup      save a copy of the original file
       -t --batch       don't ask questions in batch mode
       -u --unified     interpret the patch file as a unified diff
       -d --directory   use as current directory for interpreting filenames
       -p1              strip leading / from filenames
    """
    cmd += " %s | patch -Nbtu -p1 -d %s" % (patch, dstpath)
    executil.system(cmd)

def main():
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], "")

    except getopt.GetoptError, e:
        usage(e)

    if not len(args) == 2:
        usage()
    
    patch = args[0]
    dstpath = args[1]

    if not os.path.isfile(patch):
        fatal("does not exist: " + patch)

    if not os.path.isdir(dstpath):
        fatal("does not exist: " + dstpath)

    apply_patch(patch, dstpath)

        
if __name__=="__main__":
    main()

