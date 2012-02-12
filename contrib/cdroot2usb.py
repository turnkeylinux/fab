#!/usr/bin/python
"""
Put cdroot onto usb device

Example usage:
    shh# cdroot2usb.py build/cdroot /dev/sdb

"""
import os
import sys
import getopt
import shutil

from os.path import *

import executil
import temp

#todo:
#  check, and reset mbr?

def usage(s=None):
    if s is not None:
        print "error: " + str(s)

    print "Syntax: %s <cdroot> <usbdev>" % sys.argv[0]
    print __doc__.strip()
    
    sys.exit(1)

class Error(Exception):
    pass

class Cdroot:
    def __init__(self, path, dirs):
        self.path = realpath(path)

        for dir in dirs:
            if not exists(join(path, dir)):
                 raise Error('does not exist: %s' % join(path, dir))

class Partition:
    def __init__(self, s):
        fields = s.split(None, 7)
        if not len(fields) == 8:
            raise Error('unexpected structure')

        self.path = fields[0]

        self.is_bootable = False
        if fields[1] == '*':
            self.is_bootable = True
            fields.pop(1)  # remove bootable field, not present if not bootable

        self.start = fields[1]
        self.end = fields[2]
        self.blocks = fields[3]
        self.id = fields[4]
        self.fs = fields[5]

class UsbDev:
    def __init__(self, path, filesystem_ids):
        self.path = self._get_blockdev_path(path)

        if self.is_mounted():
            raise Error('usbdev is mounted')

        self.bootpart = self._get_bootable_partition()
        if self.bootpart is None:
            raise Error('no bootable partition found on device')

        if self.bootpart.id not in filesystem_ids:
            raise Error('bootable partition type not allowed',
                        filesystem_ids,
                        self.bootpart.id)

    @staticmethod
    def _get_blockdev_path(path):
        p = executil.getoutput("udevinfo -q path -n %s" % path).lstrip('/')
        for path in ( join('/sys', p , 'device'), 
                      join('/sys/block', basename(p)), 
                      join('/dev', basename(p)) ):
            if not exists(path):
                raise Error('usbdev path error: %s' % path)

        return join('/dev', basename(p))

    @staticmethod
    def _read_partition_table(path):
        partitions = []
        for line in executil.getoutput("fdisk -l %s" % path).splitlines():
            if line.startswith(path):
                partitions.append(Partition(line))

        return partitions

    def _get_bootable_partition(self):
        for partition in self._read_partition_table(self.path):
            if partition.is_bootable:
                return partition
    
        return None

    def is_mounted(self):
        mounts = file("/proc/mounts").read()
        if mounts.find(self.path) != -1:
            return True

        return False

    def install_bootloader(self):
        if self.is_mounted():
            raise Error('unmount usbdev to install boot loader')

        print "* installing bootloader"
        executil.system('syslinux', self.bootpart.path)

class Cdroot2Usbdev:
    def __init__(self, cdroot, usbdev):
        self.cdroot = cdroot
        self.usbdev = usbdev

        self.mountdir = temp.TempDir(dir='/media')
        self._mount()
    
    def copy(self):
        print "* copying cdroot"
        executil.system('cp -r %s/* %s' % (self.cdroot.path,
                                           self.mountdir.path))

    def isolinux2syslinux(self):
        print "* making isolinux configuration compatible for syslinux"
        path = self.mountdir.path
        executil.system('mv %s/isolinux/* %s' % (path, path))
        executil.system('mv %s/isolinux.cfg %s/syslinux.cfg' % (path, path))
        executil.system('rmdir %s/isolinux' % path)
        executil.system('rm -f %s/isolinux.bin' % path)

    def _mount(self):
        print "* mounting %s %s" % (self.usbdev.bootpart.path,
                                    self.mountdir.path)
        executil.system("mount", self.usbdev.bootpart.path, self.mountdir.path)

    def _umount(self):
        if self.usbdev.is_mounted():
            print "* umounting %s" % self.usbdev.bootpart.path
            executil.system("umount", self.usbdev.bootpart.path)

    def __del__(self):
        self._umount()

def main():
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], "", [])
    except getopt.GetoptError, e:
        usage(e)

    if not args:
        usage()

    if len(args) != 2:
        usage("bad number of arguments")

    cdroot = Cdroot(path=args[0], dirs=('casper', 'isolinux'))
    usbdev = UsbDev(path=args[1], filesystem_ids=('16')) # Hidden FAT16

    c2u = Cdroot2Usbdev(cdroot, usbdev)
    c2u.copy()
    c2u.isolinux2syslinux()
    del c2u  # we want to make sure __del__ is called

    usbdev.install_bootloader()


if __name__ == "__main__":
    main()

