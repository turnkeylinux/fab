import sys
import os
import pty
import termios

def tty_echo_off(fd):
    new = termios.tcgetattr(fd)
    new[3] = new[3] & ~termios.ECHO          # lflags
    termios.tcsetattr(fd, termios.TCSANOW, new)

pid, fd = pty.fork()
if not pid:
    line = sys.stdin.readline()
    print "ping: " + line,

    sys.exit(0)

tty_echo_off(fd)
fh = os.fdopen(fd, "r+", 0)
print >> fh, "sent"

while True:
    buf = fh.read()
    print "=== START"
    print buf
    print "=== END"
    break

fh.close()
os.waitpid(pid, 0)
