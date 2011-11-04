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
from common import fatal, warn, mkdir, get_tmpdir

@help.usage(__doc__)
def usage():
    print >> sys.stderr, "Syntax: %s [-options] <removelist> <srcpath>" % sys.argv[0]

def parse_list(raw):
    remove = []
    restore = []
    
    for expr in raw.splitlines():
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

def _move(entry, srcpath, dstpath):
    entry = entry.lstrip("/")
    src = join(srcpath, entry)
    dst = join(dstpath, dirname(entry))

    if exists(src):
        mkdir(dirname(dst))
        shutil.move(src, dst)
    else:
        warn("entry does not exist: " + entry)

def apply_removelist(removelist_fh, root_path):
    remove, restore = parse_list(removelist_fh.read())

    tmpdir = get_tmpdir()
    
    # move entries out of root_path
    for entry in remove:
        _move(entry, root_path, tmpdir)

    # move entries back into root_path
    for entry in restore:
        _move(entry, tmpdir, root_path)

    shutil.rmtree(tmpdir)

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

