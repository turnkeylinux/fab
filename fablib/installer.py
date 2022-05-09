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
from os.path import join, exists, basename
import shutil
from typing import (
        Iterable, Optional, Dict, Tuple, List, TextIO, IO, AnyStr, cast
)
import logging
logger = logging.getLogger('fab.installer')

import hashlib
from debian import debfile

from chroot import Chroot
from fablib import common


class Error(Exception):
    pass


class RevertibleFile:
    """File that automatically reverts to previous state on destruction
       or if the revert method is invoked"""

    @staticmethod
    def _get_orig_path(path: str) -> str:
        i = 1
        while True:
            orig_path = f"{path}.orig.{i}"
            if not exists(orig_path):
                return orig_path

            i += 1

    def __init__(self, path: str):
        self.orig_path: Optional[str] = None
        if exists(path):
            self.orig_path = self._get_orig_path(path)
            shutil.move(path, self.orig_path)
        self.path: Optional[str] = path

        self._inner = open(path, 'w')

    def revert(self) -> None:
        ''' revert file to original state '''
        if self.orig_path is not None:
            assert self.path is not None
            shutil.move(self.orig_path, self.path)
            self.orig_path = None
            self.path = None
        elif self.path is not None:
            os.remove(self.path)
            self.path = None

    def write(self, text: str) -> None:
        self._inner.write(text)

    def close(self) -> None:
        self._inner.close()

    def __del__(self) -> None:
        self.revert()
        self._inner.close()


class RevertibleScript(RevertibleFile):
    ''' RevertibleFile that ensures file is executable '''
    def __init__(self, path: str, lines: Iterable[str]):
        super().__init__(path)
        self.write("\n".join(lines))
        self.close()
        assert self.path is not None
        os.chmod(self.path, 0o755)


class Installer:
    def __init__(
            self, chroot_path: str,
            environ: dict[str, str] = None
    ):
        if environ is None:
            environ = {}
        env = {"DEBIAN_FRONTEND": "noninteractive", "DEBIAN_PRIORITY": "critical"}
        env.update(environ)

        self.chroot = Chroot(chroot_path, environ=env)

    @staticmethod
    def _get_packages_priority(packages: list[str]) -> tuple[list[str], list[str]]:
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

    def _install(
            self, packages: list[str],
            ignore_errors: list[str] = None,
            extra_apt_args: list[str] = None) -> None:

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

        for packages in (high, regular):
            if packages:
                args = ["-o", "Debug::pkgProblemResolver=true", "install", "--assume-yes"]
                args.extend(extra_apt_args)
                apt_return_code = self.chroot.system(
                        f"apt-get {' '.join((args + packages))}")
                if apt_return_code != 0:

                    def get_last_log(path: str) -> list[str]:
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

                    def get_errors(log: list[str], error_str: str) -> list[str]:
                        errors = []
                        for line in reversed(log):
                            if line == error_str:
                                break

                            errors.append(basename(line).split("_")[0])
                        return errors

                    log = get_last_log(join(self.chroot.path, "var/log/apt/term.log"))

                    error_str = "Errors were encountered while processing:"
                    if error_str not in log:
                        # XXX Hack to workaround apt not writing log file when
                        # experiencing 'E: Unable to locate package ...'
                        # This may have unexpected side effects?!
                        # TODO Implement proper fix to collect stdout (in
                        # turnkey-chroot) and check that for 'E: ...' messages
                        if apt_return_code == 100:
                            # always seems to return 100 when hitting
                            # 'E: Unable to locate package ...'
                            raise Error(
                                    'Errors encountered installing packages')
                        else:
                            continue

                    errors: Iterable[str] = get_errors(log, error_str)

                    ignored_errors = set(errors) & set(ignore_errors)
                    errors = set(errors) - set(ignore_errors)

                    if ignored_errors:
                        print(
                            "Warning: ignoring package installation errors (%s)"
                            % " ".join(ignored_errors)
                        )

                    if errors:
                        for error in errors:
                            common.error(error)
                        raise Error('package installation errors')

        defer_log = join(self.chroot.path, defer_log)
        if exists(defer_log):
            kversion = "all"
            boot_path = join(self.chroot.path, "boot")
            for f in os.listdir(boot_path):
                if f.startswith("vmlinuz-"):
                    kversion = f.replace("vmlinuz-", "")
                    break

            if exists(join(boot_path, f"initrd.img-{kversion}")):
                if self.chroot.system("update-initramfs -u") != 0:
                    self.chroot.system("live-update-initramfs -u")
            else:
                if self.chroot.system(
                        f"update-initramfs -c -k {kversion}") != 0:
                    self.chroot.system(f"live-update-initramfs -c -k {kversion}")

            os.remove(defer_log)

    def install(
            self, packages: list[str],
            ignore_errors: list[str] = None) -> None:
        raise NotImplementedError()


class PoolInstaller(Installer):
    def __init__(
            self, chroot_path: str, pool_path: str,
            arch: str, environ: dict[str, str] = None):
        super(PoolInstaller, self).__init__(chroot_path, environ)

        from pool_lib import Pool

        logger.debug("initializing pool")
        self.pool = Pool(pool_path)
        logger.debug("pool initialized")
        self.arch = arch

    @staticmethod
    def _get_package_index(packagedir: str) -> list[str]:
        def filesize(path: str) -> str:
            return str(os.stat(path).st_size)

        def md5sum(path: str) -> str:
            with open(path, 'rb') as fob:
                return str(hashlib.md5(fob.read()).hexdigest())

        def sha256sum(path: str) -> str:
            with open(path, 'rb') as fob:
                return str(hashlib.sha256(fob.read()).hexdigest())

        index = []
        for package in os.listdir(packagedir):
            path = os.path.join(packagedir, package)
            # dl_path would best be calculated; but we don't have access to chroot_path here...
            dl_path = os.path.join("var/cache/apt/archives", package)
            if path.endswith(".deb"):
                control = debfile.DebFile(path).debcontrol()
                for field in list(control.keys()):
                    index.append(field + ": " + control[field])

                index.append("Filename: " + dl_path)
                index.append("Size: " + filesize(path))
                index.append("MD5sum: " + md5sum(path))
                index.append("SHA256: " + sha256sum(path))
                index.append("")

        return index

    def install(
            self, packages: list[str],
            ignore_errors: list[str] = None
    ) -> None:
        """install packages into chroot via pool"""

        if ignore_errors is None:
            ignore_errors = []

        print("getting packages...")
        packagedir = join(self.chroot.path, "var/cache/apt/archives")
        logger.debug(f"{packagedir=}")
        logger.debug(f"{packages=}")
        self.pool.get(packagedir, packages, strict=True)

        print("generating package index...")
        sources_list = RevertibleFile(join(self.chroot.path, "etc/apt/sources.list"))
        # making RevertibleFile a truly compliant TextIO is a high-effort,
        # low-reward action. Here we just need it to support .write, so we
        # pretend it is a full TextIO object.
        print("deb file:/// local debs", file=cast(TextIO, sources_list))
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
    def __init__(
            self, chroot_path: str,
            apt_proxy: str = None,
            environ: dict[str, str] = None):
        super(LiveInstaller, self).__init__(chroot_path, environ)

        self.apt_proxy = apt_proxy

    def install(
            self, packages: list[str],
            ignore_errors: list[str] = None) -> None:
        """install packages into chroot via live apt"""
        if ignore_errors is None:
            ignore_errors = []

        # For v17.x I've moved the apt setting to common. I think that is the
        # right place for it, but haven't 100% committed yet. For now I'm
        # leaving this here commented...
        #if self.apt_proxy:
        #    print("setting apt proxy settings...")
        #    conf_path = join(self.chroot.path, "etc/apt/apt.conf.d/01proxy")
        #    with open(conf_path, "w") as fob:
        #        fob.write('Acquire::http::Proxy "%s";\n' % self.apt_proxy)

        print("updating package lists...")
        self.chroot.system("apt-get update")

        print("installing packages...")
        self._install(packages, ignore_errors)
