#!/usr/bin/python3
# Copyright (c) TurnKey GNU/Linux - https://www.turnkeylinux.org
#
# This file is part of Fab
#
# Fab is free software; you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by the
# Free Software Foundation; either version 3 of the License, or (at your
# option) any later version.

"""
Make release deb package.

Arguments:

    path/to/changelog       Source for latest package name and version
    path/to/output          Path to output destination
     
        If this is a file, we create the debian archive at this path.
        If this is a directory, in it we create package_version_arch.deb

Options:

    --dep=[DEPEND]          Add depend to control
"""
import os
from os.path import *

import sys
import shutil
import getopt

import re
from string import Template

from tempfile import TemporaryDirectory
import subprocess

CONTROL_TPL = """\
Package: $NAME
Version: $VERSION
Architecture: all
Maintainer: $MAINTAINER
Installed-Size: 4
Section: misc
Priority: optional
Depends: $DEPENDS
Description: $NAME release
"""

class Error(Exception):
    pass

def usage(e=None):
    if e:
        print("Error: " + str(e), file=sys.stderr)

    print("Syntax: %s path/to/changelog path/to/output" % sys.argv[0], file=sys.stderr)
    print(__doc__.strip(), file=sys.stderr)

    sys.exit(1)

def parse_changelog(path):
    with open(path) as fob:
        firstline = fob.readline()
    m = re.match('^(\w[-+0-9a-z.]*) \((\S+)\)', firstline)
    if not m:
        raise Error("can't parse first line of changelog:\n" + firstline)

    name, version = m.groups()

    with open(path) as fob:
        for line in fob:
            if not line.startswith(" -- "):
                continue

            break

    m = re.match(r' -- (.* <.*?>)', line)
    if not m:
        raise Error("can't parse maintainer:\n" + line)
    maintainer = m.group(1)

    return name, version, maintainer

def make_release_deb(path_changelog, path_output, depends=[]):
    name, version, maintainer = parse_changelog(path_changelog)

    with TemporaryDirectory() as tmpdir:
        os.mkdir(join(tmpdir, "DEBIAN"))
        with open(join(tmpdir, "DEBIAN/control"), "w") as fob:
            content = Template(CONTROL_TPL).substitute(NAME=name,
                                                       VERSION=version,
                                                       MAINTAINER=maintainer,
                                                       DEPENDS=", ".join(depends))
            print(re.sub("Depends: \n", "", content), end=' ', file=fob)

        tmpdir_doc = join(tmpdir, "usr/share/doc/" + name)
        os.makedirs(tmpdir_doc)

        shutil.copy(path_changelog, tmpdir_doc)
        subprocess.run(["dpkg-deb", "-b", tmpdir, path_output])

def main():
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], 'h', ['dep='])
    except getopt.GetoptError as e:
        usage(e)

    if len(args) != 2:
        usage()

    depends=[]
    for opt, val in opts:
        if opt == '-h':
            usage()

        if opt == '--dep':
            depends.append(val)

    path_changelog, path_output = args
    make_release_deb(path_changelog, path_output, depends)

if __name__ == "__main__":
    main()
