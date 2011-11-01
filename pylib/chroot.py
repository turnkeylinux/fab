
import os
from os.path import *

import paths
import executil

class Error(Exception):
    pass

def chrootmounts(method):
    """decorator for mountpoints
       mount/umount proc and dev/pts into/from chroot
    """
    def wrapper(self, *args, **kws):
        mounted_proc_now = False
        mounted_devpts_now = False
        
        proc_path = join(self.path, 'proc')
        devpts_path = join(self.path, 'dev/pts')

        if self.chrootmounts:
            if not self._is_mounted(proc_path):
                self._mount('proc-chroot', proc_path, '-tproc')
                mounted_proc_now = True

            if not self._is_mounted(devpts_path):
                self._mount('devpts-chroot', devpts_path, '-tdevpts')
                mounted_devpts_now = True

        try:
            ret = method(self, *args, **kws)
        finally:
            if mounted_proc_now:
                self._umount(proc_path)

            if mounted_devpts_now:
                self._umount(devpts_path)

        return ret

    return wrapper

class Chroot:
    def __init__(self, path, chrootmounts=True):
        if os.getuid() != 0:
            raise Error("root privileges required for chroot")

        self.path = realpath(path)
        self.chrootmounts = chrootmounts

    @staticmethod
    def _is_mounted(dir):
        mounts = file("/proc/mounts").read()
        if mounts.find(dir) != -1:
            return True
        return False

    @classmethod
    def _mount(cls, device, mountpath, options=None):
        args = [device, mountpath]
        if options:
            args.append(options)
            
        executil.system("mount", *args)

    @classmethod
    def _umount(cls, device):
        executil.system("umount", "-f", device)

    @chrootmounts
    def execute(self, command, get_stdout=False):
        """execute system command in chroot"""
        args = ['/usr/bin/env', '-i', 'HOME=/root', 'TERM=${TERM}', 'LC_ALL=C',
                'PATH=/usr/sbin:/usr/bin:/sbin:/bin',
                'DEBIAN_FRONTEND=noninteractive',
                'DEBIAN_PRIORITY=critical']

        chroot_args = (self.path, 'sh', '-c', " ".join(args) + " " + command)

        if get_stdout:
            return executil.getoutput("chroot", *chroot_args)
        else:
            print "chroot %s %s" % (paths.make_relative(os.getcwd(), self.path),
                                    command)
            executil.system("chroot", *chroot_args)


