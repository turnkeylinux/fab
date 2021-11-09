#!/usr/bin/python3
# Copyright (c) TurnKey GNU/Linux - http://www.turnkeylinux.org
#
# This file is part of Fab
#
# Fab is free software; you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by the
# Free Software Foundation; either version 3 of the License, or (at your
# option) any later version.

"""
Prints turnkey version by parsing changelog.

Arguments:

    path/to/changelog       Source for latest package name and version
    architecture            Architecture of build (e.g., i386 / amd64)

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
        print("error: " + str(e), file=sys.stderr)

    print("Syntax: %s path/to/changelog architecture" % sys.argv[0], file=sys.stderr)
    sys.exit(1)

class Error(Exception):
    pass

def fatal(s):
    print("error: " + str(s), file=sys.stderr)
    sys.exit(1)

def parse_changelog(fpath):
    if not os.path.exists(fpath):
        raise Error("changelog does not exist '%s'" % fpath)

    with open(fpath) as fob:
        firstline = fob.readline()
    m = re.match(r'(\S+) \((.*?)\) (\w+);', firstline)
    if not m:
        raise Error("couldn't parse changelog '%s'" % fpath)

    name, version, dist = m.groups()
    return name, version, dist

def get_turnkey_version(fpath, architecture, dist_override=None, version_tag=''):
    codename, version, dist = parse_changelog(fpath)

    if dist_override:
        dist = dist_override

    return "%s%s-%s-%s" % (codename, version_tag, dist, architecture)

def main():
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], 'h',
                                       ['dist=', 'tag='])
    except getopt.GetoptError as e:
        usage(e)

    if len(args) != 2:
        usage("incorrect number of arguments")

    changelog_path = args[0]
    architecture = args[1]
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
        print(get_turnkey_version(changelog_path, architecture, dist_override, version_tag))
    except Error as e:
        fatal(e)

if __name__=="__main__":
    main()

