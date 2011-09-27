import re
from utils import fatal, getoutput

def extract_control(path):
    return getoutput("ar -p %s control.tar.gz | zcat | tar -O -xf - control ./control 2>/dev/null" % path)

def parse_control(content):
    return dict([ re.split("\s*:\s+", line, 1)
        for line in content.split("\n")
            if not line.startswith(" ") ])

def parse_depends(content, delimeter=","):
    depends = []
    for d in content.split(delimeter):
        m = re.match("(.*) \((.*) (.*)\)", d.strip())
        if m:
            depends.append((m.group(1), m.group(3), m.group(2)))
        else:
            depends.append((d.strip(), '', ''))
    
    return depends
    
def parse_filename(filename):
    if not filename.endswith(".deb"):
        fatal("not a package `%s'" % filename)

    name, version = filename.split("_")[:2]

    return name, version

def parse_name(name):
    #TODO: solve the provides/virtual issue properly
    virtuals = {'awk':                       'mawk',
                'perl5':                     'perl',
                'perlapi-5.8.7':             'perl-base',
                'perlapi-5.8.8':             'perl-base',
                'mail-transport-agent':      'postfix',
                'libapt-pkg-libc6.4-6-3.53': 'apt',
                'aufs-modules':              'aufs-modules-2.6.20-15-386'
               }

    if name in virtuals:
        return virtuals[name]
    
    return name

def is_preinstall(name):
    if name.startswith("linux-image"):
        return True
    
    return False
