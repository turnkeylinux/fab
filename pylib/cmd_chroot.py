#!/usr/bin/python
"""Executes commands in a new root

Options:
  -s --script=PATH	 Run script inside chroot
  
"""
import os
from os.path import *
import paths

import sys
import getopt
import tempfile
import shutil

import help
from chroot import Chroot
from common import fatal

@help.usage(__doc__)
def usage():
    print >> sys.stderr, "Syntax: %s <newroot> [ command ... ]" % sys.argv[0]
    print >> sys.stderr, "Syntax: %s <newroot> --script path/to/executable [ args ]" % sys.argv[0]

def chroot_script(newroot, script_path, *args):
    if not isfile(script_path):
        fatal("not a file: " + script_path)

    chroot = Chroot(newroot)
    tmpdir = tempfile.mkdtemp(dir=join(chroot.path, "tmp"),
                              prefix="chroot-script.")

    script_path_chroot = join(tmpdir, basename(script_path))
    shutil.copy(script_path, script_path_chroot)
    
    os.chmod(script_path_chroot, 0755)
    chroot.system(paths.make_relative(chroot.path, script_path_chroot),
                  *args)
    shutil.rmtree(tmpdir)

def main():
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], 's:', [ 'script=' ])
    except getopt.GetoptError, e:
        usage(e)

    script_path = None
    for opt, val in opts:
        if opt in ('-s', '--script'):
            script_path = val

    if not args:
        usage()
    
    newroot = args[0]
    args = args[1:]
    
    if not isdir(newroot):
        fatal("not a directory: " + newroot)

    if script_path:
        chroot_script(newroot, script_path, *args)
        
    else:
        if not args:
            args = ('/bin/bash',)

        Chroot(newroot).system(*args)

if __name__=="__main__":
    main()

