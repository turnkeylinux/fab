#!/usr/bin/python

import os
import re
import sys

import commands

class Error(Exception):
    pass

def usage(s=None):
    if s: print >> sys.stderr, s
    print >> sys.stderr, "Syntax: %s release target repo spec" % os.path.basename(sys.argv[0])
    sys.exit(1)

def system(command, *args):
    command = command + " " + " ".join([commands.mkarg(arg) for arg in args])
    err = os.system(command)
    if err:
        raise Error("command failed: " + command,
                    os.WEXITSTATUS(err))

def parse_bootstrap_spec(raw):
    required  = []
    base = []
    sections = {"# REQUIRED": required,
                "# BASE":     base}
    for line in raw:
        line = line.strip()
        if line in sections:
            section = sections[line]
            continue

        if line:
            name, version = line.split("=")
            section.append(name)

    return required, base

def main():
    if len(sys.argv) != 5:
        usage()

    release = sys.argv[1]
    target = sys.argv[2]
    repo = sys.argv[3]
    spec = sys.argv[4]

    if not os.path.isabs(repo):
        usage("repository must be absoluate path: " + repo)

    raw = file(spec, "r").readlines()
    required, base = parse_bootstrap_spec(raw)
 
    os.environ["REQUIRED_PACKAGES"] = " ".join(required)
    os.environ["BASE_PACKAGES"] = " ".join(base)

    system("debootstrap --arch i386 %s %s file://%s" % (release, target, repo))


if __name__=="__main__":
    main()
