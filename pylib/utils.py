
import os
import re
import sys
import commands
import subprocess

class Error(Exception):
    pass

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
