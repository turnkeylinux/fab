
import os
from os.path import *

import deb
import executil

def is_mounted(dir):
    mounts = file("/proc/mounts").read()
    if mounts.find(dir) != -1:
        return True
    return False

def mount(device, mountp, options=None):
    if not is_mounted(device):
        print "mounting: " + device
        if options:
            executil.system("mount", device, mountp, options)
        else:
            executil.system("mount", device, mountp)

def umount(device):
    if is_mounted(device):
        print "umounting: " + device
        executil.system("umount", "-f", device)

class Error(Exception):
    pass

class Chroot:
    """class for interacting with a fab chroot"""
    def __init__(self, path):
        if os.getuid() != 0:
            raise Error("root privileges required for chroot")

        self.path = path
    
    def mountpoints(self):
        """mount proc and dev/pts into chroot"""
        mount('proc-chroot',   join(self.path, 'proc'),    '-tproc')
        mount('devpts-chroot', join(self.path, 'dev/pts'), '-tdevpts')

    def umountpoints(self):
        """umount proc and dev/pts from chroot"""
        umount(join(self.path, 'dev/pts'))
        umount(join(self.path, 'proc'))

    def system_chroot(self, command, get_stdout=False):
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

    def _insert_fakestartstop(self):
        """insert fake start-stop-daemon into chroot"""
        daemon = join(self.path, 'sbin/start-stop-daemon')
        if isfile('%s.REAL' % daemon): #already created
            return
        
        executil.system("mv %s %s.REAL" % (daemon, daemon))
        
        fake = "#!/bin/sh\n" \
               "echo\n" \
               "echo \"Warning: Fake start-stop-daemon called, doing nothing\"\n"
        
        open(daemon, "w").write(fake)
        os.chmod(daemon, 0755)

    def _remove_fakestartstop(self):
        """remove fake start-stop daemon from chroot"""
        daemon = join(self.path, 'sbin/start-stop-daemon')
        executil.system("mv %s.REAL %s" % (daemon, daemon))

    def _apt_indexpath(self):
        """return package index path"""
        return join(self.path,
                    "var/lib/apt/lists",
                    "_dists_local_debs_binary-i386_Packages")

    def _apt_sourcelist(self):
        """configure apt for local index generation and package installation"""
        source = "deb file:/// local debs"
        path = join(self.path, "etc/apt/sources.list")
        file(path, "w").write(source)
    
    def _apt_refresh(self, pkgdir_path):
        """generate index cache of packages in pkgdir_path"""
        self._apt_sourcelist()       
        
        print "generating package index..."
        executil.system("apt-ftparchive packages %s > %s" % (pkgdir_path, 
                                                    self._apt_indexpath()))
        self.system_chroot("apt-cache gencaches")
        
    def apt_install(self, pkgdir_path):
        """install pkgdir_path/*.deb packages into chroot"""
        self._apt_refresh(pkgdir_path)
        
        pkgnames = []
        pre_pkgnames = []
        for filename in os.listdir(pkgdir_path):
            if filename.endswith(".deb"):
                name, version = filename.split("_")[:2]
                if deb.is_preinstall(name):
                    pre_pkgnames.append(name)
                else:
                    pkgnames.append(name)
        
        self._insert_fakestartstop()
        
        for pkglist in [pre_pkgnames, pkgnames]:
            pkglist.sort()
            self.system_chroot("apt-get install -y --allow-unauthenticated %s" %
                               " ".join(pkglist))

        self._remove_fakestartstop()

    def apt_clean(self):
        """clean apt cache in chroot"""
        self.system_chroot("apt-get clean")
        executil.system("rm -f " + self._apt_indexpath())


