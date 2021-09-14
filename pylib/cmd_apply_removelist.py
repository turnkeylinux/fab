#!/usr/bin/python
# Copyright (c) TurnKey GNU/Linux - http://www.turnkeylinux.org
#
# This file is part of Fab
#
# Fab is free software; you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by the
# Free Software Foundation; either version 3 of the License, or (at your
# option) any later version.

"""Remove files and folders according to removelist

Arguments:
  <removelist>      Path to read removelist from (- for stdin)
                    Entries may be negated by prefixing a `!'
  <root>            Root path relative to which we remove entries
"""

import os
from os.path import join, exists, dirname
import re
import sys
import shutil

import help
from temp import TempDir

from common import fatal, warn, mkdir


@help.usage(__doc__)
def usage():
    print("Syntax: %s [-options] <removelist> <srcpath>" % sys.argv[0], file=sys.stderr)


def parse_removelist(s):
    remove = []
    restore = []

    for expr in s.splitlines():
        expr = re.sub(r"#.*", "", expr)
        expr = expr.strip()
        if not expr:
            continue

        if expr.startswith("!"):
            entry = expr[1:]
            restore.append(entry)

        else:
            entry = expr
            remove.append(entry)

    return remove, restore


def _move(entry, source_root_path, dest_root_path):
    entry = entry.strip("/")
    source_path = join(source_root_path, entry)
    dest_path = join(dest_root_path, entry)

    if not exists(source_path):
        warn("entry does not exist: " + entry)
        return

    mkdir(dirname(dest_path))
    shutil.move(source_path, dest_path)


def apply_removelist(removelist_fh, root_path):
    remove, restore = parse_removelist(removelist_fh.read())

    tmpdir = TempDir()

    # move entries out of root_path
    for entry in remove:
        _move(entry, root_path, tmpdir.path)

    # move entries back into root_path
    for entry in restore:
        _move(entry, tmpdir.path, root_path)


def main():
    args = sys.argv[1:]
    if len(args) != 2:
        usage()

    removelist, root_path = args
    if removelist == "-":
        removelist_fh = sys.stdin
    else:
        removelist_fh = open(args[0], "r")

    try:
        if not os.path.isdir(root_path):
            fatal("root path does not exist: " + root_path)

        apply_removelist(removelist_fh, root_path)
    finally:
        removelist_fh.close()


if __name__ == "__main__":
    main()
