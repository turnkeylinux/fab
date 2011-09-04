import sys

def usage(doc):
    def decor(print_syntax):
        def wrapper(err=None):
            if err:
                print >> sys.stderr, "error: %s" % err
            print_syntax()
            if doc:
                print >> sys.stderr, doc.strip()
            sys.exit(1)
        return wrapper
    return decor


        
    
