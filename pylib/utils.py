
import os
import sys
import commands
import subprocess

from executil import system

class Error(Exception):
    pass

def fatal(s):
    print >> sys.stderr, "FATAL: " + str(s)
    sys.exit(1)

def warning(s):
    print >> sys.stderr, "WARNING: " + str(s)

def mkdir(path):
    path = str(path)
    if not os.path.exists(path):
        os.makedirs(path)

def system_pipe(command, pipein, quiet=False):
    if quiet:
        p = subprocess.Popen(command,
                             stdin = subprocess.PIPE,
                             stdout = subprocess.PIPE,
                             #stderr = subprocess.PIPE,
                             close_fds = True)
    else:
        p = subprocess.Popen(command,
                             stdin = subprocess.PIPE,
                             close_fds = True)
        
    out, err =  p.communicate(pipein)
    if p.returncode != 0:
        raise Error("failed command: " + " ".join(command))
    
    return out, err
