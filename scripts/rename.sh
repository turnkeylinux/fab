#!/bin/sh

set -e

if [[ $# != 1 ]]; then
    echo syntax: $0 newname
    exit 1
fi

progname=$1
cat Makefile | \
awk 'BEGIN {p = 1} /^init:/ { p=0 } /^updatelinks:/ { p=1} p { print }' | \
sed "s/make init/make rename/; \
     s/^progname=.*/progname=$progname/" > Makefile.tmp
mv Makefile.tmp Makefile

sed -i -e "s/^progname=.*/progname=$progname/" debian/rules

sed -i -e "s/^Source:.*/Source: $progname/; \
           s/^Package:.*/Package: $progname/; \
           s/^Maintainer:.*/Maintainer: $GIT_AUTHOR_NAME <$GIT_AUTHOR_EMAIL>/" debian/control

progchar=$(echo $progname | awk '{ print substr($1,1,1) }')
sed -i -e "s/^REPODST=.*/REPODST=private\/$progchar\/$progname/" debian/pkginfo

$(dirname $0)/updatelinks.sh
