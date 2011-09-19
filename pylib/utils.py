
import os
import re
import sys
import commands
import subprocess

class Error(Exception):
    pass

def fatal(s):
    print >> sys.stderr, "FATAL: " + str(s)
    sys.exit(1)

def mkdir_parents(path, mode=0777):
    """mkdir 'path' recursively (I.e., equivalent to mkdir -p)"""
    path = str(path)
    dirs = path.split("/")
    for i in range(2, len(dirs) + 1):
        dir = "/".join(dirs[:i+1])
        if os.path.isdir(dir):
            continue
        os.mkdir(dir, mode)

def read_filehandle(fh):
    ret = ""
    for line in fh.readlines():
        ret += line
    return ret

def system(command, *args):
    command = command + " " + " ".join([commands.mkarg(arg) for arg in args])
    err = os.system(command)
    if err:
        raise Error("command failed: " + command,
                    os.WEXITSTATUS(err))

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
    return out, err

def getstatus(command):
    (s,o) = commands.getstatusoutput(command)
    return s

def getoutput(command):
    (s,o) = commands.getstatusoutput(command)
    return o
