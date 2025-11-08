#!/usr/bin/python3
# Copyright (c) 2013 Alon Swartz <alon@turnkeylinux.org>
#
# This file is part of Fab
#
# Fab is free software; you can redistribute it and/or modify it under the
# terms of the GNU Affero General Public License as published by the Free
# Software Foundation; either version 3 of the License, or (at your option) any
# later version.

"""
iso2usb: Create a bootable USB flash drive containing ISO image

Arguments:
    iso_path        Path to ISO (e.g., product.iso)
    usb_device      USB device path (e.g., /dev/sdc)

Options:
    --force         Not implemented, interactive confirmation required

Warnings:
    - Be very sure the USB device is correct, abort if unsure!!

    - If ISO is not hybrid mode, it will be converted after confirmation.
      This will alter the image, you might want to make a copy before hand.
"""

import getopt
import os
import stat
import subprocess
import sys
from typing import NoReturn


class Error(Exception):
    pass


def fatal(message: str | Error | getopt.GetoptError) -> NoReturn:
    print(f"Error: {message}", file=sys.stderr)
    sys.exit(1)


def usage(message: str | getopt.GetoptError | None = None) -> NoReturn:
    if message:
        print(f"Error: {message}", file=sys.stderr)

    cmd = os.path.basename(sys.argv[0])
    print(f"Syntax: {cmd} iso_path usb_device", file=sys.stderr)
    print(__doc__.strip(), file=sys.stderr)

    sys.exit(1)


class Iso:
    def __init__(self, path: str) -> None:
        self.path = os.path.realpath(path)
        self.name = os.path.basename(self.path)

        if not os.path.exists(self.path):
            raise Error(f"iso path does not exist: {self.path}")

    def make_hybrid(self) -> None:
        subprocess.run(["isohybrid", self.path])

        if not self.is_hybrid:
            raise Error("iso not verified as hybrid mode")

    @property
    def is_hybrid(self) -> bool:
        output = subprocess.run(
            ["fdisk", "-l", self.path], capture_output=True, text=True
        ).stdout

        if "Hidden HPFS/NTFS" in output:
            return True

        if "Disk identifier: 0x00000000" in output:
            return False

        if "doesn't contain a valid partition table" in output:
            return False

        raise Error("unable to determine ISO hybrid status")


class Usb:
    def __init__(self, path: str) -> None:
        self.path = path

        if not os.path.exists(self.path):
            raise Error(f"usb path does not exist: {self.path}")

        if not self.is_block_device:
            raise Error(f"usb path is not a block device: {self.path}")

        if self.is_partition:
            raise Error(f"usb path seems to be a partition: {self.path}")

        if not self.is_usb_device:
            raise Error(
                f"usb path is not verifiable as a usb device: {self.path}"
            )

    @property
    def is_block_device(self) -> bool:
        mode = os.stat(self.path).st_mode
        return stat.S_ISBLK(mode)

    @property
    def is_partition(self) -> bool:
        try:
            int(self.path[-1])
            return True
        except ValueError:
            return False

    @property
    def is_usb_device(self) -> bool:
        if "usb" in self.name:
            return True
        return False

    @property
    def name(self) -> str:
        cmd = ["udevadm", "info", "-q", "symlink", "-n", self.path]
        output = subprocess.run(cmd, text=True).stdout
        return output.split(" ")[0]

    def write_iso(self, iso_path: str) -> None:
        cmd = ["dd", f"if={iso_path}", f"of={self.path}"]
        subprocess.run(cmd)


def main() -> None:
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], "h", ["help"])
    except getopt.GetoptError as e:
        usage(e)

    for opt, _val in opts:
        if opt in ("-h", "--help"):
            usage()

    if not len(args) == 2:
        usage()

    if os.geteuid() != 0:
        fatal("root privileges are required")

    try:
        iso = Iso(args[0])
        usb = Usb(args[1])
    except Error as e:
        fatal(e)

    print("*" * 78)
    print(f"iso: {iso.name} (hybrid: {iso.is_hybrid})")
    print(f"usb: {usb.name} ({usb.path})")
    print("*" * 78)

    cont = input("Is the above correct? (y/N): ").strip()
    if not cont.lower() == "y":
        fatal("aborting...")

    if not iso.is_hybrid:
        print("processing ISO for hybrid mode...")
        iso.make_hybrid()

    print("writing ISO to USB, this could take a while...")
    usb.write_iso(iso.path)


if __name__ == "__main__":
    main()
