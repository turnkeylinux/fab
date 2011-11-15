#!/usr/bin/python
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

SALTCHARS = './abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';

def random_salt():
    return "".join([SALTCHARS[random.randint(0, len(SALTCHARS) - 1)] for i in range(2)])

def fatal(s):
    print >> sys.stderr, "error: " + str(s)
    sys.exit(1)

def usage():
    print "Syntax: %s" % sys.argv[0]
    print __doc__.strip()
    
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

    print crypt.crypt(password, random_salt())
        
if __name__ == "__main__":
    main()

