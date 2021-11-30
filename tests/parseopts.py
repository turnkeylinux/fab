import sys
import getopt

opts, args = getopt.getopt(sys.argv[1:], "I:D:")

for opt, val in opts:
    if opt == '-I':
        print("INCLUDE: " + val)
    elif opt == '-D':
        print("DEFINE: " + val)
    
