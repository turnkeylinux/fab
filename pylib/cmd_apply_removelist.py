#!/usr/bin/python
"""Remove files and folders according to removelist

Arguments:
  <removelist>      Path to read removelist from (- for stdin)
                    Entries may be negated by prefixing a `!'
  <root>            Root path relative to which we remove entries
"""

import os
import re
import sys
import shutil
import getopt
from os.path import *

import help
import executil
from temp import TempDir

from common import fatal, warn, mkdir

@help.usage(__doc__)
def usage():
    print >> sys.stderr, "Syntax: %s [-options] <removelist> <srcpath>" % sys.argv[0]

def parse_removelist(s):
    remove = []
    restore = []
    
    for expr in s.splitlines():
        expr = re.sub(r'#.*', '', expr)
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
    if removelist == '-':
        removelist_fh = sys.stdin
    else:
        removelist_fh = file(args[0], "r")

    if not os.path.isdir(root_path):
        fatal("root path does not exist: " + root_path)

    apply_removelist(removelist_fh, root_path)
        
if __name__=="__main__":
    main()

