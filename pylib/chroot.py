
import os
from os.path import *

import paths
import executil

class Error(Exception):
    pass

class MagicMounts:
    class Paths(paths.Paths):
        files = [ "proc", "dev/pts" ]
        
    def __init__(self, root="/"):
        self.paths = self.Paths(root)

        self.mounted_proc_myself = False
        self.mounted_devpts_myself = False

        self.mount()

    @staticmethod
    def _is_mounted(dir):
        mounts = file("/proc/mounts").read()
        if mounts.find(dir) != -1:
            return True
        return False

    def mount(self):
        if not self._is_mounted(self.paths.proc):
            executil.system("mount -t proc", "proc-chroot", self.paths.proc)
            self.mounted_proc_myself = True

        if not self._is_mounted(self.paths.dev.pts):
            executil.system("mount -t devpts", "devpts-chroot", self.paths.dev.pts)
            self.mounted_devpts_myself = True

    def umount(self):
        if self.mounted_devpts_myself:
            executil.system("umount", self.paths.dev.pts)
            self.mounted_devpts_myself = False

        if self.mounted_proc_myself:
            executil.system("umount", self.paths.proc)
            self.mounted_proc_myself = False

    def __del__(self):
        self.umount()

class Chroot:
    def __init__(self, newroot, environ={}):
        if os.getuid() != 0:
            raise Error("root privileges required for chroot")

        self.environ = { 'HOME': '/root',
                         'TERM': os.environ['TERM'],
                         'LC_ALL': 'C',
                         'PATH': "/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/bin:/usr/sbin" }
        self.environ.update(environ)

        self.path = realpath(newroot)
        self.magicmounts = MagicMounts(self.path)

    def _prepare_command(self, *command):
        env = ['env', '-i' ] + [ name + "=" + val
                                 for name, val in self.environ.items() ]

        command = executil.fmt_command(*command)
        return ("chroot", self.path, 'sh', '-c', " ".join(env) + " " + command)
    
    def system(self, *command):
        """execute system command in chroot -> None"""
        executil.system(*self._prepare_command(*command))

    def getoutput(self, *command):
        return executil.getoutput(*self._prepare_command(*command))



