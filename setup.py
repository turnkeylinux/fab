#!/usr/bin/python3

from distutils.core import setup

setup(
    name="fab",
    version="1.0",
    author="Stefan Davis",
    author_email="stefan@turnkeylinux.org",
    url="https://github.com/turnkeylinux/fab",
    packages=["fablib"],
    scripts=["fab"]
)
