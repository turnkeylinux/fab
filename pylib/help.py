# Copyright (c) TurnKey Linux - http://www.turnkeylinux.org
#
# This file is part of Fab
#
# Fab is free software; you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by the
# Free Software Foundation; either version 3 of the License, or (at your
# option) any later version.

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


        
    
