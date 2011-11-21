import os
import md5
import shutil
from os.path import *

import debinfo
import executil
from chroot import Chroot
from pyproject.pool.pool import Pool

class Error(Exception):
    pass

def get_package_index(packagedir):
    def filesize(path):
        return str(os.stat(path).st_size)

    def md5sum(path):
        return str(md5.md5(open(path, 'rb').read()).hexdigest())

    index = []
    for package in os.listdir(packagedir):
        path = os.path.join(packagedir, package)
        if path.endswith('.deb'):
            control = debinfo.get_control_fields(path)
            for field in control.keys():
                index.append(field + ": " + control[field])

            index.append("Filename: " + path)
            index.append("Size: " + filesize(path))
            index.append("MD5sum: " + md5sum(path))
            index.append("")

    return index

class RevertibleFile(file):
    """File that automatically reverts to previous state on destruction
       or if the revert method is invoked"""
    @staticmethod
    def _get_orig_path(path):
        i = 1
        while True:
            orig_path = "%s.orig.%d" % (path, i)
            if not exists(orig_path):
                return orig_path

            i += 1
    
    def __init__(self, path):
        self.orig_path = None
        if exists(path):
            self.orig_path = self._get_orig_path(path)
            shutil.move(path, self.orig_path)
        self.path = path

        file.__init__(self, path, "w")

    def revert(self):
        if self.orig_path:
            shutil.move(self.orig_path, self.path)
            self.orig_path = None
            self.path = None
        elif self.path:
            os.remove(self.path)
            self.path = None
            
    def __del__(self):
        self.revert()

class Installer:
    def __init__(self, chroot_path, pool_path):
        self.chroot = Chroot(chroot_path,
                             environ={'DEBIAN_FRONTEND': 'noninteractive',
                                      'DEBIAN_PRIORITY': 'critical'})
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
        self.chroot.system("apt-get clean")
        os.remove(indexfile)

    def _apt_genindex(self, packagedir, indexfile):
        index = get_package_index(packagedir)
        file(indexfile, "w").write("\n".join(index))

        self.chroot.system("apt-cache gencaches")

    def _apt_install(self, packages):
        high, regular = self._prioritize_packages(packages)

        sources_list = RevertibleFile(join(self.chroot.path, "etc/apt/sources.list"))
        print >> sources_list, "deb file:/// local debs"
        sources_list.close()

        fake_start_stop = RevertibleFile(join(self.chroot.path, "sbin/start-stop-daemon"))
        fake_start_stop.write("#!/bin/sh\n" +
                              "echo\n" +
                              "echo \"Warning: Fake start-stop-daemon called\"\n")
        fake_start_stop.close()
        os.chmod(fake_start_stop.path, 0755)

        defer_log = "var/lib/update-initramfs.deferred"
        fake_update_initramfs = RevertibleFile(join(self.chroot.path, "usr/sbin/update-initramfs"))
        fake_update_initramfs.write("#!/bin/sh\n" +
                                    "echo\n" +
                                    "echo \"Warning: Deferring update-initramfs $@\"\n" +
                                    "echo \"update-initramfs $@\" >> /%s\n" % defer_log)
        fake_update_initramfs.close()
        os.chmod(fake_update_initramfs.path, 0755)

        for packages in (high, regular):
            if packages:
                args = ['install', '--force-yes', '--assume-yes', '--allow-unauthenticated']
                self.chroot.system("apt-get", *(args + packages))

        fake_update_initramfs.revert()
        defer_log = join(self.chroot.path, defer_log)
        if exists(defer_log):
            deferred = [ command.strip()
                         for command in file(defer_log, 'r').readlines() ]
            for command in set(deferred):
                self.chroot.system(command)

            os.remove(defer_log)
            
    def install(self, packages):
        """install packages into chroot """
        packagedir = join(self.chroot.path, "var/cache/apt/archives")
        indexfile  = join(self.chroot.path, "var/lib/apt/lists",
                          "_dists_local_debs_binary-i386_Packages")

        print "getting packages..."
        self.pool.get(packagedir, packages, strict=True)

        print "generating package index..."
        self._apt_genindex(packagedir, indexfile)

        print "installing packages..."
        self._apt_install(packages)
        self._apt_clean(indexfile)

