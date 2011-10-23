
import os
import shutil
from os.path import *

import deb
import executil
from chroot import Chroot
from pool import Pool

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

    @fakestartstop
    @sources_list
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

