#!/usr/bin/python
"""Example command template

Options:
  -q --quiet	don't print anything

  -f=FOO	print FOO

  --warn	print a warning
  --fatal       fatal error

"""
import sys
import help
import getopt

@help.usage(__doc__)
def usage():
    print >> sys.stderr, "Syntax: %s [args]" % sys.argv[0]

exitcode = 0
def warn(s):
    global exitcode
    exitcode = 1

    print >> sys.stderr, "example: " + str(s)

def fatal(s):
    warn(s)
    sys.exit(1)

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'qf:h', ['warn',
                                                          'fatal'])
    except getopt.GetoptError, e:
        usage(e)

    opt_quiet = False
    for opt, val in opts:
        if opt == '-h':
            usage()

        if opt in ('-q', '--quiet'):
            opt_quiet = True

        elif opt == '-f':
            print "printing foo: " + val

        elif opt == '--warn':
            warn("this is a warning")

        elif opt == '--fatal':
            fatal("fatal condition")

    if not opt_quiet:
        print "printing args: " + `args`

    sys.exit(exitcode)
    
if __name__=="__main__":
    main()

