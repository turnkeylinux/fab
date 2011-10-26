
import os
from os.path import *

import executil

class Error(Exception):
    pass

def chrootmounts(method):
    """decorator for mountpoints
       mount/umount proc and dev/pts into/from chroot
    """
    def wrapper(self, *args, **kws):
        if self.chrootmounts:
            self._mount('proc-chroot',   join(self.path, 'proc'),   '-tproc')
            self._mount('devpts-chroot', join(self.path, 'dev/pts'),'-tdevpts')

        try:
            ret = method(self, *args, **kws)
        finally:
            if self.chrootmounts:
                self._umount(join(self.path, 'dev/pts'))
                self._umount(join(self.path, 'proc'))

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
    def _mount(cls, device, mountp, options=None):
        if not cls._is_mounted(device):
            print "mounting: " + device
            if options is not None:
                executil.system("mount", device, mountp, options)
            else:
                executil.system("mount", device, mountp)

    @classmethod
    def _umount(cls, device):
        if cls._is_mounted(device):
            print "umounting: " + device
            executil.system("umount", "-f", device)

    @chrootmounts
    def execute(self, command, get_stdout=False):
        """execute system command in chroot"""
        args = ['/usr/bin/env', '-i', 'HOME=/root', 'TERM=${TERM}', 'LC_ALL=C',
                'PATH=/usr/sbin:/usr/bin:/sbin:/bin',
                'DEBIAN_FRONTEND=noninteractive',
                'DEBIAN_PRIORITY=critical']

        command = " ".join(args) + " " + command
        chroot_args = (self.path, 'sh', '-c', command)

        if get_stdout:
            return executil.getoutput("chroot", *chroot_args)
        else:
            executil.system("chroot", *chroot_args)


