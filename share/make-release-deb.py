#!/usr/bin/python
"""
Make release deb package.

Arguments:

    path/to/changelog       Source for latest package name and version
    path/to/output          Path to output destination
     
        If this is a file, we create the debian archive at this path.
        If this is a directory, in it we create package_version_arch.deb

"""
import os
from os.path import *

import sys
import shutil

import re
from string import Template

from temp import TempDir
from executil import system

CONTROL_TPL = """\
Package: $NAME
Version: $VERSION
Architecture: all
Maintainer: Liraz Siri <liraz@turnkeylinux.org>
Installed-Size: 4
Section: misc
Priority: optional
Description: $NAME release
"""

class Error(Exception):
    pass

def usage(e=None):
    if e:
        print >> sys.stderr, "Error: " + str(e)

    print >> sys.stderr, "Syntax: %s path/to/changelog path/to/output" % sys.argv[0]
    print >> sys.stderr, __doc__.strip()

    sys.exit(1)

def parse_changelog(path):
    firstline = file(path).readline()
    m = re.match('^(\w[-+0-9a-z.]*) \((\S+)\)', firstline)
    if not m:
        raise Error("can't parse first line of changelog:\n" + firstline)

    name, version = m.groups()
    return name, version

def make_release_deb(path_changelog, path_output):
    name, version = parse_changelog(path_changelog)

    tmpdir = TempDir()
    os.mkdir(join(tmpdir.path, "DEBIAN"))
    control = file(join(tmpdir.path, "DEBIAN/control"), "w")
    print >> control, Template(CONTROL_TPL).substitute(NAME=name, 
                                                       VERSION=version),
    control.close()

    tmpdir_doc = join(tmpdir.path, "usr/share/doc/" + name)
    os.makedirs(tmpdir_doc)

    shutil.copy(path_changelog, tmpdir_doc)
    system("dpkg-deb -b", tmpdir.path, path_output)

def main():
    args = sys.argv[1:]
    if len(args) != 2:
        usage()

    path_changelog, path_output = args
    make_release_deb(path_changelog, path_output)

if __name__ == "__main__":
    main()
