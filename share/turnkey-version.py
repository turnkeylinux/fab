#!/usr/bin/python
"""
Prints turnkey version by parsing changelog.

Arguments:

    distro                  Base distribution (e.g., lucid)
    path/to/changelog       Source for latest package name and version

Options:

    --dist=DISTRO           Override changelog distribution
    --tag=VERSION_TAG       Append tag to version (e.g., rc)
"""

import os
import re
import sys
import getopt

def usage(e=None):
    if e:
        print >> sys.stderr, "error: " + str(e)

    print >> sys.stderr, "Syntax: %s path/to/changelog" % sys.argv[0]
    sys.exit(1)

class Error(Exception):
    pass

def fatal(s):
    print >> sys.stderr, "error: " + str(s)
    sys.exit(1)

def parse_changelog(fpath):
    if not os.path.exists(fpath):
        raise Error("changelog does not exist '%s'" % fpath)

    firstline = file(fpath).readline()
    m = re.match(r'(\S+) \((.*?)\) (\w+);', firstline)
    if not m:
        raise Error("couldn't parse changelog '%s'" % fpath)
    
    name, version, dist = m.groups()
    return name, version, dist

def get_turnkey_version(fpath, dist_override=None, version_tag=''):
    codename, version, dist = parse_changelog(fpath)

    if dist_override:
        dist = dist_override

    return "%s%s-%s-x86" % (codename, version_tag, dist)
 
def main():
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], 'h',
                                       ['dist=', 'tag='])
    except getopt.GetoptError, e:
        usage(e)

    if len(args) != 1:
        usage("incorrect number of arguments")

    changelog_path = args[0]
    dist_override = None
    version_tag = ''
    for opt, val in opts:
        if opt == '-h':
            usage()

        if opt == '--dist':
            dist_override = val

        if opt == '--tag':
            version_tag = val

    try:
        print get_turnkey_version(changelog_path, dist_override, version_tag)
    except Error, e:
        fatal(e)
    
if __name__=="__main__":
    main()

