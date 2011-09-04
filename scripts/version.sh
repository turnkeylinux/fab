#!/bin/bash
# calculate the version according to the current working git repository
# if we can, we use git-describe to calculate version from the most recent tag
# otherwise, we calculate a version based on the last commit

installed_path=$(dirname $0)
unset CDPATH
cd $installed_path

if git_version=$(git-describe HEAD 2>/dev/null); then
    echo $git_version
else
    if last_commit=$(git-rev-parse HEAD 2>/dev/null); then
	    unixtime=$(git-show --quiet --pretty=format:%at $last_commit)
	    date=$(date -ud "1970-01-01 UTC + $unixtime sec" +%F)

	    echo $date.${last_commit:0:8}
    else
	echo "error: can't determine version"
	exit 1
    fi
fi

