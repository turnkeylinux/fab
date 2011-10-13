#!/usr/bin/python
# Copyright (c) 2011 TurnKey Linux - all rights reserved
"""
Configuration environment variables:
    FAB_PLAN_INCLUDE_PATH   Global include path for plan preprocessing
    FAB_POOL_PATH           Lookup path for a relative pool path
    FAB_TMPDIR              Temporary storage (defaults to /var/tmp)
"""

import re
import sys
import os
import imp
import getopt
import version

COPYRIGHT="version %s (c) 2011 TurnKey Linux - all rights reserved"

# location of our python modules
PATH_LIB="pylib"

# location of our executables (relative to the install path)
PATH_LIBEXEC="libexec"

# this variable allows you to optionally specify the order commands
# are printed in Commands.usage()
COMMANDS_USAGE_ORDER = ['cpp', 'chroot', 'chroot-umount', 'spec-get', '',

                        'plan-resolve', 'spec-install',
                        'apply-removelist', 'apply-overlay']

def get_copyright():
    return COPYRIGHT % version.get_version()

# this function is designed to work when running in-place source
# and when running code through a pycompiled installation with execproxy
def get_av0():
    try:
        cmdline = file("/proc/%d/cmdline" % os.getpid(), "r").read()
        args = cmdline.split("\x00")
        if re.match(r'python[\d\.]*$', os.path.basename(args[0])):
            av0 = args[1]
        else:
            av0 = args[0]
                    
    except IOError:
        av0 = sys.argv[0]

    return os.path.basename(av0)

def fatal(e):
    print >> sys.stderr, "fatal: " + str(e)
    sys.exit(1)
    
class Commands:
    class Error(Exception):
        pass
    
    class Command:
        def __init__(self, name, module):
            self.name = name
            self.module = module
            self.desc = ""
            self.doc = ""
            
            doc = module.__doc__
            if doc:
                self.doc = doc.strip()
                self.desc = self.doc.split('\n')[0]
            
    def _find_commands(self):
        commands = set()
        for file in os.listdir(self.path):
            m = re.match(r'^cmd_(.*)\.py[co]?$', file)
            if not m:
                continue
            command = m.group(1)
            command = command.replace("_", "-")

            commands.add(command)

        return commands

    def _get_module(self, command_name):
        module_name = "cmd_" + command_name.replace("-", "_")
        module_args = imp.find_module(module_name, [ self.path ])
        module = imp.load_module(module_name, *module_args)

        return module

    def __init__(self, path):
        self.path = path
        self.commands = {}
        self.use_debugger = False
        self.use_profiler = False

        for command_name in self._find_commands():
            module = self._get_module(command_name)
            self.commands[command_name] = self.Command(command_name, module)

        # if there's only one command, patch its usage to show copyright
        if len(self.commands) == 1:
            command = self.commands.values()[0]
            module = command.module
            usage = getattr(module, "usage", None)
            if usage:
                def wrapper(*args):
                    print >> sys.stderr, get_copyright()
                    return usage(*args)
                module.usage = wrapper

    def usage(self, error=None):
        print >> sys.stderr, get_copyright()
        if error:
            print >> sys.stderr, "error: " + str(error)
           
        print >> sys.stderr, "Syntax: %s <command> [args]" % os.path.basename(get_av0())
        if __doc__:
            print __doc__
        print >> sys.stderr, "Commands:"
        def print_command(name):
            command = self.commands.get(name)
            if command:
                print >> sys.stderr, "    %s    %s" % (command.name.ljust(maxlen),
                                                       command.desc)
        command_names = self.get_names()
        maxlen = max([len(name) for name in command_names])
        for name in COMMANDS_USAGE_ORDER:
            if name == '':
                print
                continue
            print_command(name)

        command_names = list(set(command_names) - set(COMMANDS_USAGE_ORDER))
        command_names.sort()
        for name in command_names:
            print_command(name)
            
        sys.exit(1)

    def get(self, name):
        return self.commands.get(name)

    def get_names(self):
        return self.commands.keys()

    def exists(self, name):
        return self.commands.has_key(name)

    def _pre_run(self, name, args):
        sys.argv = [ name ] + args
        command = self.get(name)

        i = 1
        while i < len(sys.argv):
            if sys.argv[i] == "--profile":
                self.use_profiler = True
                del sys.argv[i]
            elif sys.argv[i] == "--debug":
                self.use_debugger = True
                del sys.argv[i]
            else:
                i += 1

        if '-h' in args or '--help' in args:
            try:
                command.module.usage()
            except AttributeError:
                print >> sys.stderr, "error: no help for " + name
                sys.exit(1)

        return command
        
    def run(self, name, args):
        command = self._pre_run(name, args)

        if self.use_profiler and self.use_debugger:
            raise self.Error("can't use both profiler and debugger")

        is_running_suid = os.getuid() != os.geteuid()
        if is_running_suid and self.use_debugger:
            raise self.Error("won't allow debugger while running suid")

        if self.use_debugger:
            self._debug(command)
        elif self.use_profiler:
            self._profile(command)
        else:
            command.module.main()

    def _debug(self, command):
        import pdb
        pdb.runcall(command.module.main)

    def _profile(self, command):
        import profile
        import pstats
        import tempfile

        statsfile = tempfile.mkstemp(".prof")[1]
        profile.runctx('command.module.main()', globals(), locals(), statsfile)
        pstats.Stats(statsfile).strip_dirs().sort_stats('cumulative').print_stats()
        
        os.remove(statsfile)
        
    def __len__(self):
        return len(self.commands)
    
def main():
    if "--version" in sys.argv:
        print version.get_version()
        sys.exit(0)

    install_path = os.path.dirname(__file__)
    if PATH_LIBEXEC:
        os.environ['PATH'] = os.path.join(install_path, PATH_LIBEXEC) + ":" + \
                             os.environ['PATH']
    
    pylib_path = os.path.join(install_path, PATH_LIB)
    sys.path.insert(0, pylib_path)

    commands = Commands(pylib_path)
    if len(commands) > 1:
        av0 = get_av0()

        # project-name? (symbolic link)
        try:
            name = av0[av0.index('-') + 1:]
            args = sys.argv[1:]
        except ValueError:
            try:
                opts, args = getopt.getopt(sys.argv[1:], 'pdh')
            except getopt.GetoptError, e:
                commands.usage(e)

            for opt, val in opts:
                if opt == '-h':
                    commands.usage()
                if opt == '-p':
                    commands.use_profiler = True
                elif opt == '-d':
                    commands.use_debugger = True

            if not args:
                commands.usage()
            
            name = args[0]
            args = args[1:]

        if not commands.exists(name):
            commands.usage("no such name '%s'" % name)

    else:
        name = commands.get_names()[0]
        args = sys.argv[1:]

    try:
        commands.run(name, args)
    except commands.Error, e:
        fatal(e)
    
if __name__=='__main__':
    main()
