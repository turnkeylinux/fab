#!/usr/bin/python
# Copyright (c) TurnKey GNU/Linux - http://www.turnkeylinux.org
#
# This file is part of Fab
#
# Fab is free software; you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by the
# Free Software Foundation; either version 3 of the License, or (at your
# option) any later version.

"""
Encrypt user-provided password with crypt(3)

Example usage:
  ./cryptpass.py > crypthash     # prompts for password
  echo password | ./cryptpass.py 

"""
import os
import sys
import crypt
import getpass
import random

from typing import NoReturn

SALTCHARS = './abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';

def random_salt() -> str:
    return "".join([SALTCHARS[random.randint(0, len(SALTCHARS) - 1)] for i in range(2)])

def fatal(s: Any) -> NoReturn:
    print("error: " + str(s), file=sys.stderr)
    sys.exit(1)

def usage() -> NoReturn:
    print("Syntax: %s" % sys.argv[0])
    print(__doc__.strip())
    
    sys.exit(1)

def main():
    if '-h' in sys.argv:
        usage()

    if os.isatty(sys.stdin.fileno()):
        password = getpass.getpass("Password: ")
        if not password:
            fatal("empty password")
            
        if getpass.getpass("Confirm: ") != password:
            fatal("passwords don't match")
    else:
        password = sys.stdin.readline().rstrip("\n")

    print(crypt.crypt(password, random_salt()))
        
if __name__ == "__main__":
    main()

