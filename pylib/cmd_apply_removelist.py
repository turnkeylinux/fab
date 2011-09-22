#!/usr/bin/python
"""Remove files and folders according to removelist

Arguments:
  <removelist>      Path to read removelist from (- for stdin)
                    Entries may be negated by prefixing a `!'
  <srcpath>         Path containing removelist entries (ie. chroot)

Options:
  --dstpath=        Path to directory which will store removed items
                    If not specified, FAB_TMPDIR will be used
"""


import re
import os
import sys
import help
import getopt
from os.path import *

import fab
from utils import *


@help.usage(__doc__)
def usage():
    print >> sys.stderr, "Syntax: %s [-options] <removelist> <srcpath>" % sys.argv[0]

def parse_list(raw):
    list = {'yes': [],
            'no':  []}
    
    for line in raw.split("\n"):
        line = re.sub(r'#.*', '', line)
        line = line.strip()
        if not line:
            continue
        m = re.match("!(.*)", line)
        if m:
            list['no'].append(m.group(1))
        else:
            list['yes'].append(line)

    return list

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
        input = sys.stdin
    else:
        input = file(args[0], "r")

    raw = read_filehandle(input)
    rmlist = parse_list(raw)
    
    srcpath = args[1]

    if not isdir(srcpath):
        fatal("srcpath does not exist: " + srcpath)

    opt_dstpath = None
    for opt, val in opts:
        if opt == '--dstpath':
            opt_removedir.append(val)

    fab.apply_removelist(rmlist, srcpath, opt_dstpath)

        
if __name__=="__main__":
    main()

