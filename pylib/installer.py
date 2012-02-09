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

class RevertibleScript(RevertibleFile):
    def __init__(self, path, lines):
        RevertibleFile.__init__(self, path)
        self.write("\n".join(lines))
        self.close()
        os.chmod(self.path, 0755)

class RevertibleInitctl(RevertibleScript):
    @staticmethod
    def _get_dummy_path():
        # ugly hack to support running fab from source directory
        source_path = join(dirname(dirname(__file__)), 'share/initctl.dummy')
        if exists(source_path):
            return source_path
        return "/usr/share/fab/share/initctl.dummy"

    def _divert(self, action):
        """actions: add, remove"""
        cmd = "dpkg-divert --local --rename --%s /sbin/initctl >/dev/null" % action
        self.chroot.system(cmd)

    def __init__(self, chroot):
        self.chroot = chroot
        self._divert('add')
        path = join(self.chroot.path, "sbin/initctl")
        content = file(self._get_dummy_path()).read()
        RevertibleScript.__init__(self, path, content.splitlines())

    def revert(self):
        RevertibleScript.revert(self)
        self._divert('remove')

class Installer:
    def __init__(self, chroot_path, pool_path, environ={}):
        env = {'DEBIAN_FRONTEND': 'noninteractive',
               'DEBIAN_PRIORITY': 'critical'}
        env.update(environ)

        self.chroot = Chroot(chroot_path, environ=env)
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

    def _apt_install(self, packages, ignore_errors=[]):
        high, regular = self._prioritize_packages(packages)

        sources_list = RevertibleFile(join(self.chroot.path, "etc/apt/sources.list"))
        print >> sources_list, "deb file:/// local debs"
        sources_list.close()

        lines = [ "#!/bin/sh", 
                  "echo", 
                  "echo \"Warning: Fake invoke-rc.d called\"" ]
        fake_invoke_rcd = RevertibleScript(join(self.chroot.path, "usr/sbin/invoke-rc.d"), lines)

        lines = [ "#!/bin/sh", 
                  "echo", 
                  "echo \"Warning: Fake start-stop-daemon called\"" ]
        fake_start_stop = RevertibleScript(join(self.chroot.path, "sbin/start-stop-daemon"), lines)

        defer_log = "var/lib/update-initramfs.deferred"
        lines = [ "#!/bin/sh", 
                  "echo", 
                  "echo \"Warning: Deferring update-initramfs $@\"", 
                  "echo \"update-initramfs $@\" >> /%s" % defer_log ]
        fake_update_initramfs = RevertibleScript(join(self.chroot.path, "usr/sbin/update-initramfs"), lines)

        fake_initctl = RevertibleInitctl(self.chroot)

        for packages in (high, regular):
            if packages:
                try:
                    args = ['install', '--force-yes', '--assume-yes', '--allow-unauthenticated']
                    self.chroot.system("apt-get", *(args + packages))
                except executil.ExecError, e:
                    def get_last_log(path):
                        log = []
                        for line in reversed(file(path).readlines()):
                            if line.startswith("Log ended: "):
                                continue
                            if line.startswith("Log started: "):
                                break
                            log.append(line.strip())

                        log.reverse()
                        return log

                    def get_errors(log, error_str):
                        errors = []
                        for line in reversed(log):
                            if line == error_str:
                                break

                            errors.append(basename(line).split("_")[0])
                        return errors

                    log = get_last_log(join(self.chroot.path, "var/log/apt/term.log"))

                    error_str = "Errors were encountered while processing:"
                    if error_str not in log:
                        raise

                    errors = get_errors(log, error_str)

                    ignored_errors = set(errors) & set(ignore_errors)
                    errors = set(errors) - set(ignore_errors)

                    if ignored_errors:
                        print "Warning: ignoring package installation errors (%s)" % " ".join(ignored_errors)

                    if errors:
                        raise

        fake_update_initramfs.revert()
        defer_log = join(self.chroot.path, defer_log)
        if exists(defer_log):
            kversion = ""
            boot_path = join(self.chroot.path, "boot")
            for f in os.listdir(boot_path):
                if f.startswith("vmlinuz-"):
                    kversion = f.replace("vmlinuz-", "")
                    break

            if not exists(join(boot_path, "initrd.img-%s" % kversion)):
                self.chroot.system("update-initramfs -c -k %s" % kversion)
            else:
                self.chroot.system("update-initramfs -u")

            os.remove(defer_log)
            
    def install(self, packages, ignore_errors=[]):
        """install packages into chroot """
        packagedir = join(self.chroot.path, "var/cache/apt/archives")
        indexfile  = join(self.chroot.path, "var/lib/apt/lists",
                          "_dists_local_debs_binary-i386_Packages")

        print "getting packages..."
        self.pool.get(packagedir, packages, strict=True)

        print "generating package index..."
        self._apt_genindex(packagedir, indexfile)

        print "installing packages..."
        self._apt_install(packages, ignore_errors)
        self._apt_clean(indexfile)

