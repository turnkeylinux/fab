#!/usr/bin/python

import os
import sys
from os.path import *

from executil import system

def usage(s=None):
    if s: print >> sys.stderr, s
    print >> sys.stderr, "Syntax: %s suite target path/to/repo required_spec base_spec" % basename(sys.argv[0])
    sys.exit(1)

def get_packages(spec_file):
    return [ line.split("=")[0] 
             for line in file(spec_file).readlines() ]

def main():
    args = sys.argv[1:]
    if len(args) != 5:
        usage()

    suite, target, repo, required_spec, base_spec = args

    os.environ["REQUIRED_PACKAGES"] = " ".join(get_packages(required_spec))
    os.environ["BASE_PACKAGES"] = " ".join(get_packages(base_spec))
    repo = abspath(repo)

    system("debootstrap --arch i386 %s %s file://%s" % (suite, target, repo))

if __name__=="__main__":
    main()
