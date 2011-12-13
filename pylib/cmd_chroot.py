#!/usr/bin/python
"""Executes commands in a new root

Options:
  -s --script=PATH	     Run script inside chroot
  -e --env=VARNAME[: ...]    List of environment variable names to pass through
                             default: $FAB_CHROOT_ENV

Usage examples:
  chroot path/to/chroot echo hello
  chroot path/to/chroot "ls -la /"
  chroot path/to/chroot -- ls -la /
  chroot path/to/chroot --script scripts/printargs arg1 arg2

  FOO=bar BAR=foo chroot path/to/chroot -e FOO:BAR env
  
"""
import os
from os.path import *
import paths

import sys
import getopt
import tempfile
import shutil

import help
from chroot import Chroot as _Chroot
from common import fatal, get_environ

from executil import ExecError

class Chroot(_Chroot):
    def system(self, *command):
        try:
            _Chroot.system(self, *command)
        except ExecError, e:
            return e.exitcode

        return 0

@help.usage(__doc__)
def usage():
    print >> sys.stderr, "Syntax: %s [ -options ] <newroot> [ command ... ]" % sys.argv[0]
    print >> sys.stderr, "Syntax: %s [ -options ] <newroot> --script path/to/executable [ args ]" % sys.argv[0]

def chroot_script(chroot, script_path, *args):
    if not isfile(script_path):
        fatal("no such script (%s)" % script_path)

    tmpdir = tempfile.mkdtemp(dir=join(chroot.path, "tmp"),
                              prefix="chroot-script.")

    script_path_chroot = join(tmpdir, basename(script_path))
    shutil.copy(script_path, script_path_chroot)
    
    os.chmod(script_path_chroot, 0755)
    err = chroot.system(paths.make_relative(chroot.path, script_path_chroot),
                        *args)
    shutil.rmtree(tmpdir)

    return err

def main():
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], 's:e:',
                                       [ 'script=', 'env=' ])
    except getopt.GetoptError, e:
        usage(e)

    env_conf = os.environ.get('FAB_CHROOT_ENV')
    
    script_path = None
    for opt, val in opts:
        if opt in ('-s', '--script'):
            script_path = val

        if opt in ('-e', '--env'):
            env_conf = val

    if not args:
        usage()
    
    newroot = args[0]
    args = args[1:]
    
    if not isdir(newroot):
        fatal("no such chroot (%s)" % newroot)

    chroot = Chroot(newroot, environ=get_environ(env_conf))
    
    if script_path:
        err = chroot_script(chroot, script_path, *args)
        sys.exit(err)
        
    else:
        if not args:
            args = ('/bin/bash',)

        err = chroot.system(*args)
        sys.exit(err)
            
if __name__=="__main__":
    main()

