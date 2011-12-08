#!/usr/bin/python

import os
import sys

from executil import system

def usage(s=None):
    if s: print >> sys.stderr, s
    print >> sys.stderr, "Syntax: %s release target path/to/repo required_spec base_spec" % os.path.basename(sys.argv[0])
    sys.exit(1)

def get_packages(spec_file):
    return [ line.split("=")[0] 
             for line in file(spec_file).readlines() ]

def main():
    if len(sys.argv) != 6:
        usage()

    release = sys.argv[1]
    target = sys.argv[2]
    repo = sys.argv[3]
    required_spec = sys.argv[4]
    base_spec = sys.argv[5]

    os.environ["REQUIRED_PACKAGES"] = " ".join(get_packages(required_spec))
    os.environ["BASE_PACKAGES"] = " ".join(get_packages(base_spec))
    repo = os.path.abspath(repo)

    system("debootstrap --arch i386 %s %s file://%s" % (release, target, repo))

if __name__=="__main__":
    main()
