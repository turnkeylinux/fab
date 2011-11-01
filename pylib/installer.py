
import os
import shutil
from os.path import *

import deb
import executil
from chroot import Chroot
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

def defer_update_initramfs(method):
    """decorator to defer and compound update-initramfs execution
       intercept calls and log them, finally execute unique calls in order
    """
    def wrapper(self, *args, **kws):
        defer_log = "var/lib/update-initramfs.deferred"

        path = join(self.chroot.path, "usr/sbin/update-initramfs")
        path_orig = path + ".orig"
        if exists(path_orig):
            raise Error("file shouldn't exist: " + path_orig)
        
        shutil.move(path, path_orig)
        defer = "#!/bin/sh\n" \
                "echo\n" \
                "echo \"Warning: Deferring update-initramfs $@\"\n" \
                "echo \"update-initramfs $@\" >> %s\n" % join("/", defer_log)

        open(path, "w").write(defer)
        os.chmod(path, 0755)

        try:
            ret = method(self, *args, **kws)
        finally:
            shutil.move(path_orig, path)
            defer_log = join(self.chroot.path, defer_log)

            executed = []
            for cmd in file(defer_log, 'r').readlines():
                cmd = cmd.strip()
                if cmd not in executed:
                    self.chroot.execute(cmd)
                    executed.append(cmd)

            os.remove(defer_log)

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

    @staticmethod
    def _prioritize_packages(packages):
        """high priority packages must be installed before regular packages
           APT should handle this, but in some circumstances it chokes...
        """
        HIGH_PRIORITY = ('linux-image')

        high = []
        regular = []

        for package in packages:
            if package.startswith(HIGH_PRIORITY):
                high.append(package)
            else:
                regular.append(package)

        return high, regular

    def _apt_clean(self, indexfile):
        self.chroot.execute("apt-get clean")
        os.remove(indexfile)

    def _apt_genindex(self, packagedir, indexfile):
        index = deb.get_package_index(packagedir)
        file(indexfile, "w").write("\n".join(index))

        self.chroot.execute("apt-cache gencaches")

    @sources_list
    @fakestartstop
    @defer_update_initramfs
    def _apt_install(self, packages):
        high, regular = self._prioritize_packages(packages)

        for packages in (high, regular):
            if packages:
                args = ['install', '--assume-yes', '--allow-unauthenticated']
                cmd = "apt-get " + " ".join(args) + " " + " ".join(packages)

                self.chroot.execute(cmd)

    def install(self, packages):
        """install packages into chroot """
        packagedir = join(self.chroot.path, "var/cache/apt/archives")
        indexfile  = join(self.chroot.path, "var/lib/apt/lists",
                          "_dists_local_debs_binary-i386_Packages")

        print "getting packages..."
        self.pool.get(packages, packagedir)

        print "generating package index..."
        self._apt_genindex(packagedir, indexfile)

        print "installing packages..."
        self._apt_install(packages)
        self._apt_clean(indexfile)

