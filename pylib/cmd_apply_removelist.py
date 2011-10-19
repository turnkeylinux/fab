#!/usr/bin/python
"""Remove files and folders according to removelist

Arguments:
  <removelist>      Path to read removelist from (- for stdin)
                    Entries may be negated by prefixing a `!'
  <srcpath>         Path containing removelist entries (ie. chroot)

Options:
  --dstpath=        Path to directory which will store removed items
                    If not specified, FAB_TMPDIR will be used, and deleted
                    when finished.
"""

import os
import re
import sys
import shutil
import getopt
from os.path import *

import help
import executil
from common import mkdir, get_tmpdir
from cli_common import fatal, warn

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
    entry = re.sub("^/","", entry)
    src = join(srcpath, entry)
    dst = join(dstpath, dirname(entry))

    if exists(src):
        mkdir(dst)
        if isdir(src):
            executil.system("mv -f %s/* %s/" % (dirname(src), dst))
        else:
            executil.system("mv -f %s %s/" % (src, dst))
    else:
        warn("entry does not exist: " + entry)

def apply_removelist(rmlist_fh, srcpath, dstpath=None):
    remove, restore = parse_list(rmlist_fh.read())

    remove_dstpath = False
    if not dstpath:
        dstpath = get_tmpdir()
        remove_dstpath = True


    # move entries out of srcpath
    for entry in remove:
        _move(entry, srcpath, dstpath)

    # move entries back into srcpath
    for entry in restore:
        _move(entry, dstpath, srcpath)

    if remove_dstpath:
        shutil.rmtree(dstpath)

def main():
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], "",
                                       ['dstpath='])
    except getopt.GetoptError, e:
        usage(e)

    if sys.argv.count("-") == 1:
        args.insert(0, "-")
    
    if not len(args) == 2:
        usage()
    
    if args[0] == '-':
        rmlist_fh = sys.stdin
    else:
        rmlist_fh = file(args[0], "r")

    srcpath = args[1]

    if not os.path.isdir(srcpath):
        fatal("srcpath does not exist: " + srcpath)

    kws = {}
    for opt, val in opts:
        kws[opt[2:]] = val

    apply_removelist(rmlist_fh, srcpath, **kws)

        
if __name__=="__main__":
    main()

