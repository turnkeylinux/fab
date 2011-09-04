#include <stdio.h>
#include <unistd.h>
#include <libgen.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>

#ifndef MODULE_PATH
#error "no MODULE_PATH defined"
#endif

void
clean_environ(void)
{
	static char def_IFS[] = "IFS= \t\n";
	static char def_PATH[] = "PATH=/sbin:/bin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin";
	static char def_CDPATH[] = "CDPATH=.";
	static char def_ENV[] = "ENV=:";

        char **p;
        extern char **environ;

        for (p = environ; *p; p++) {
                if (strncmp(*p, "LD_", 3) == 0)
                        **p = 'X';
                else if (strncmp(*p, "_RLD", 4) == 0)
                        **p = 'X';
                else if (strncmp(*p, "PYTHON", 6) == 0)
                        **p = 'X';
                else if (strncmp(*p, "IFS=", 4) == 0)
                        *p = def_IFS;
                else if (strncmp(*p, "CDPATH=", 7) == 0)
                        *p = def_CDPATH;
                else if (strncmp(*p, "ENV=", 4) == 0)
                        *p = def_ENV;
        }
        putenv(def_PATH);
}

int main(int argc, char **argv)
{
	int i;
	uid_t uid = getuid();
        uid_t euid = geteuid();

	char *argv_copy[argc + 5];

	argv_copy[0] = basename(argv[0]);
	argv_copy[1] = "-O";
	argv_copy[2] = "-E";
	argv_copy[3] = MODULE_PATH;

	for(i = 1; i < argc; i++) {
		argv_copy[i + 3] = strdup(argv[i]);
	}
	argv_copy[i + 3] = NULL;

	if(uid != euid) {
		struct stat statb;
		/*
		  Check that the owner of the script is equal to either the
		  effective uid or the super user.
		*/
		if (stat(MODULE_PATH, &statb) < 0) {
			perror("stat");
			exit(1);
		}
		if (statb.st_uid != 0 && statb.st_uid != euid) {
			fprintf(stderr, "%s: %s has the wrong owner\n", argv[0],
				MODULE_PATH);
			fprintf(stderr, "The module should be owned by root,\n");
			fprintf(stderr, "and shouldn't be writeable by anyone.\n");
			exit(1);
		}
		
		clean_environ();
	}

	execv("/usr/bin/python", argv_copy);
	perror("execv");
}
