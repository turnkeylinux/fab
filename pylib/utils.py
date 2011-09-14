
import os
import re
import sys
import commands
import subprocess

class Error(Exception):
    pass

def system(command, *args):
    command = command + " " + " ".join([commands.mkarg(arg) for arg in args])
    err = os.system(command)
    if err:
        raise Error("command failed: " + command,
                    os.WEXITSTATUS(err))

def system_pipe(command, pipein):
    p = subprocess.Popen(command,
                         stdin = subprocess.PIPE, 
                         close_fds = True)
    return p.communicate(pipein)
