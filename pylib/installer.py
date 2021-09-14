# Copyright (c) TurnKey GNU/Linux - http://www.turnkeylinux.org
#
# This file is part of Fab
#
# Fab is free software; you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by the
# Free Software Foundation; either version 3 of the License, or (at your
# option) any later version.

import io
import os
from os.path import join, exists
import shutil
import hashlib

import debian
from chroot import Chroot
from subprocess import CalledProcessError


class Error(Exception):
    pass


class RevertibleFile(io.FileIO):
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

        super().__init__(path, "w")

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
        super().__init__(path)
        self.write("\n".join(lines))
        self.close()
        os.chmod(self.path, 0o755)


class RevertibleInitctl(RevertibleScript):
    @property
    def dummy_path(self):
        fab_share = os.environ.get("FAB_SHARE_PATH", "/usr/share/fab")
        return join(fab_share, "initctl.dummy")

    def _divert(self, action):
        """actions: add, remove"""
        cmd = "dpkg-divert --local --rename --%s /sbin/initctl >/dev/null" % action
        self.chroot.system(cmd)

    def __init__(self, chroot):
        self.chroot = chroot
        self._divert("add")
        path = join(self.chroot.path, "sbin/initctl")
        with open(self.dummy_path, "r") as fob:
            content = fob.read()
        super().__init__(path, content.splitlines())

    def revert(self):
        super().revert()
        self._divert("remove")


class Installer:
    def __init__(self, chroot_path, environ=None):
        if environ is None:
            environ = {}
        env = {"DEBIAN_FRONTEND": "noninteractive", "DEBIAN_PRIORITY": "critical"}
        env.update(environ)

        self.chroot = Chroot(chroot_path, environ=env)

    @staticmethod
    def _get_packages_priority(packages):
        """high priority packages must be installed before regular packages
           APT should handle this, but in some circumstances it chokes...
        """
        HIGH_PRIORITY = "linux-image"

        high = []
        regular = []

        for package in packages:
            if package.startswith(HIGH_PRIORITY):
                high.append(package)
            else:
                regular.append(package)

        return high, regular

    def _install(self, packages, ignore_errors=None, extra_apt_args=None):
        if ignore_errors is None:
            ignore_errors = []
        if extra_apt_args is None:
            extra_apt_args = []
        high, regular = self._get_packages_priority(packages)

        lines = ["#!/bin/sh", "echo", 'echo "Warning: Fake invoke-rc.d called"']
        fake_invoke_rcd = RevertibleScript(
            join(self.chroot.path, "usr/sbin/invoke-rc.d"), lines
        )

        lines = ["#!/bin/sh", "echo", 'echo "Warning: Fake start-stop-daemon called"']
        fake_start_stop = RevertibleScript(
            join(self.chroot.path, "sbin/start-stop-daemon"), lines
        )

        defer_log = "var/lib/update-initramfs.deferred"
        lines = [
            "#!/bin/sh",
            "echo",
            'echo "Warning: Deferring update-initramfs $@"',
            'echo "update-initramfs $@" >> /%s' % defer_log,
        ]
        fake_update_initramfs = RevertibleScript(
            join(self.chroot.path, "usr/sbin/update-initramfs"), lines
        )

        fake_initctl = RevertibleInitctl(self.chroot)

        for packages in (high, regular):
            if packages:
                try:
                    args = ["install", "--assume-yes"]
                    args.extend(extra_apt_args)
                    self.chroot.system("apt-get", *(args + packages))
                except CalledProcessError:

                    def get_last_log(path):
                        log = []
                        with open(path) as fob:
                            for line in fob:
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
                        print(
                            "Warning: ignoring package installation errors (%s)"
                            % " ".join(ignored_errors)
                        )

                    if errors:
                        raise

        fake_update_initramfs.revert()
        defer_log = join(self.chroot.path, defer_log)
        if exists(defer_log):
            kversion = "all"
            boot_path = join(self.chroot.path, "boot")
            for f in os.listdir(boot_path):
                if f.startswith("vmlinuz-"):
                    kversion = f.replace("vmlinuz-", "")
                    break

            if exists(join(boot_path, "initrd.img-%s" % kversion)):
                try:
                    self.chroot.system("update-initramfs -u")
                except CalledProcessError:
                    self.chroot.system("live-update-initramfs -u")
            else:
                try:
                    self.chroot.system("update-initramfs -c -k %s" % kversion)
                except CalledProcessError:
                    self.chroot.system("live-update-initramfs -c -k %s" % kversion)

            os.remove(defer_log)


class PoolInstaller(Installer):
    def __init__(self, chroot_path, pool_path, arch, environ=None):
        super(PoolInstaller, self).__init__(chroot_path, environ)

        from pyproject.pool.pool import Pool

        self.pool = Pool(pool_path)
        self.arch = arch

    @staticmethod
    def _get_package_index(packagedir):
        def filesize(path):
            return str(os.stat(path).st_size)

        def md5sum(path):
            return str(hashlib.md5(open(path, "rb").read()).hexdigest())

        def sha256sum(path):
            return str(hashlib.sha256(open(path, "rb").read()).hexdigest())

        index = []
        for package in os.listdir(packagedir):
            path = os.path.join(packagedir, package)
            # dl_path would best be calculated; but we don't have access to chroot_path here...
            dl_path = os.path.join("var/cache/apt/archives", package)
            if path.endswith(".deb"):
                control = debian.debfile.DebFile(path).debcontrol()
                for field in list(control.keys()):
                    index.append(field + ": " + control[field])

                index.append("Filename: " + dl_path)
                index.append("Size: " + filesize(path))
                index.append("MD5sum: " + md5sum(path))
                index.append("SHA256: " + sha256sum(path))
                index.append("")

        return index

    def install(self, packages, ignore_errors=None):
        """install packages into chroot via pool"""

        if ignore_errors is None:
            ignore_errors = []

        print("getting packages...")
        packagedir = join(self.chroot.path, "var/cache/apt/archives")
        self.pool.get(packagedir, packages, strict=True)

        print("generating package index...")
        sources_list = RevertibleFile(join(self.chroot.path, "etc/apt/sources.list"))
        print("deb file:/// local debs", file=sources_list)
        sources_list.close()

        index_file = "_dists_local_debs_binary-%s_Packages" % self.arch
        index_path = join(self.chroot.path, "var/lib/apt/lists", index_file)
        index = self._get_package_index(packagedir)
        with open(index_path, "w") as fob:
            fob.write("\n".join(index))
        self.chroot.system("apt-cache gencaches")

        print("installing packages...")
        self._install(packages, ignore_errors, ["--allow-unauthenticated"])


class LiveInstaller(Installer):
    def __init__(self, chroot_path, apt_proxy=None, environ=None):
        super(LiveInstaller, self).__init__(chroot_path, environ)

        self.apt_proxy = apt_proxy

    def install(self, packages, ignore_errors=None):
        """install packages into chroot via live apt"""
        if ignore_errors is None:
            ignore_errors = []

        if self.apt_proxy:
            print("setting apt proxy settings...")
            conf_path = join(self.chroot.path, "etc/apt/apt.conf.d/01proxy")
            with open(conf_path, "w") as fob:
                fob.write('Acquire::http::Proxy "%s";\n' % self.apt_proxy)

        print("updating package lists...")
        self.chroot.system("apt-get update")

        print("installing packages...")
        self._install(packages, ignore_errors)
