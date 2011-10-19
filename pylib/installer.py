
import os
import shutil
from os.path import *

import deb
import executil
from pool import Pool

class Error(Exception):
    pass

def fakestartstop(method):
    """decorator for fake start-stop-daemon
       backup real, create fake, finally restore real
    """
    def wrapper(self, *args, **kws):
        path = join(self.chroot.path, "sbin/start-stop-daemon")
        path_orig = path + ".orig"
        if not exists(path_orig):
            shutil.move(path, path_orig)
            fake = "#!/bin/sh\n" \
                  "echo\n" \
                  "echo \"Warning: Fake start-stop-daemon called\"\n"

            open(path, "w").write(fake)
            os.chmod(path, 0755)

        try:
            ret = method(self, *args, **kws)
        finally:
            shutil.move(path_orig, path)

        return ret

    return wrapper

def sources_list(method):
    """decorator for sources.list
       backup current, create local version, finally restore current
    """
    def wrapper(self, *args, **kws):
        path = join(self.chroot.path, "etc/apt/sources.list")
        path_orig = path + ".orig"
        if not exists(path_orig):
            shutil.move(path, path_orig)
            open(path, "w").write("deb file:/// local debs\n")

        try:
            ret = method(self, *args, **kws)
        finally:
            shutil.move(path_orig, path)

        return ret

    return wrapper


class Installer:
    def __init__(self, chroot_path, pool_path):
        self.chroot = Chroot(chroot_path)
        self.pool = Pool(pool_path)

    def _apt_clean(self, indexfile):
        """clean apt cache in chroot"""
        self.chroot.execute("apt-get clean")
        os.remove(indexfile)

    def _apt_genindex(self, packagedir, indexfile):
        """generate package index"""

        print "generating package index..."
        cmd = "apt-ftparchive packages %s > %s" % (packagedir, indexfile)
        executil.system(cmd)

        self.chroot.execute("apt-cache gencaches")

    @fakestartstop
    @sources_list
    def _apt_install(self, packagedir):
        high, regular = deb.prioritize_packages(packagedir)

        for packages in (high, regular):
            args = ['install', '--assume-yes', '--allow-unauthenticated']
            command = "apt-get " + " ".join(args) + " " + " ".join(packages)

            self.chroot.execute(command)

    def install(self, packages):
        """install packages into chroot """
        packagedir = join(self.chroot.path, "var/cache/apt/archives")
        indexfile  = join(self.chroot.path, "var/lib/apt/lists",
                          "_dists_local_debs_binary-i386_Packages")

        self.pool.get(packages, packagedir)
        self._apt_genindex(packagedir, indexfile)
        self._apt_install(packagedir)
        self._apt_clean(indexfile)


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
                self.umount_chrootmounts()

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

    def umount_chrootmounts(self):
        """umount proc and dev/pts from chroot"""
        self._umount(join(self.path, 'dev/pts'))
        self._umount(join(self.path, 'proc'))

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


