import re
from utils import getoutput

def extract_control(path):
    return getoutput("ar -p %s control.tar.gz | zcat | tar -O -xf - control ./control 2>/dev/null" % path)

def parse_control(content):
    return dict([ re.split("\s*:\s+", line, 1)
        for line in content.split("\n")
            if not line.startswith(" ") ])

def parse_depends(content):
    depends = []
    for d in content.split(","):
        m = re.match("(.*) \((.*) (.*)\)", d.strip())
        if m:
            depends.append((m.group(1), m.group(3), m.group(2)))
        else:
            depends.append((d.strip(), '', ''))
    
    return depends
    
