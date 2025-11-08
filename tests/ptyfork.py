import os
import pty
import sys
import termios


def tty_echo_off(fd: int) -> None:
    new = termios.tcgetattr(fd)
    new[3] = new[3] & ~termios.ECHO  # lflags
    termios.tcsetattr(fd, termios.TCSANOW, new)


pid, fd = pty.fork()
if not pid:
    line = sys.stdin.readline()
    print(f"ping: {line}")

    sys.exit(0)

tty_echo_off(fd)
fh = os.fdopen(fd, "r+", 0)
print("sent", file=fh)

while True:
    buf = fh.read()
    print("=== START")
    print(buf)
    print("=== END")
    break

fh.close()
os.waitpid(pid, 0)
