#!/bin/bash

FAB=/turnkey/projects/fab/fab        #test development version
#FAB=fab                             #test installed version

usage() {
    echo "syntax: $0 [ --options ]"
    echo 
    echo "  If no testing options are specified - test everything"
    echo
    echo "Options:"
    echo "  --testbase=PATH use previously initialized testbase"
    echo
    echo "  --nodelete      dont delete testbase at the end"
    echo "                  (default if test fails)"
    echo 
    echo "  --planresolve   test plan-resolve"
    
    exit 1
}

if [ "$1" == "-h" ]; then
    usage
fi

testbase=""
for arg; do
    case "$arg" in
	--testbase=*)
	    testbase=${arg#--testbase=}
	    ;;
	    
	--nodelete)
	    nodelete=yes
	    ;;

        --planresolve)
	    test_planresolve=yes
            ;;

        *)
	    usage
    esac
done

OPTS="planresolve"

noopts=yes
for opt in $OPTS; do
    if [ -n "$(eval echo \$test_$opt)" ]; then
	noopts=no
    fi
done

if [ "$noopts" = "yes" ]; then
    for opt in $OPTS; do
	eval test_$opt=yes
    done
fi

set -ex
base=$(pwd)

if [ -z "$testbase" ]; then
    export TMPDIR=/turnkey/tmp/fab
    mkdir -p $TMPDIR
    testbase=$(mktemp -d -t test.XXXXXX)
fi

pool_path=$testbase/pool
export FAB_TMPDIR=$testbase/tmp

if [ ! -e "$pool_path" ]; then
    mkdir $pool_path
    cd $pool_path
    pool-init /turnkey/fab/buildroots/rocky
    cp -a $base/regtest-stocks stocks
    pool-register stocks
    cd -
fi

if [ -n "$test_planresolve" ]; then
    echo p1 | $FAB plan-resolve - $pool_path
    $FAB plan-resolve $base/regtest-plans/plan1 $pool_path

    echo f1 | $FAB plan-resolve - $pool_path || true
    echo f2 | $FAB plan-resolve - $pool_path || true
    echo f3 | $FAB plan-resolve - $pool_path || true
fi

if [ -z "$nodelete" ]; then
    echo === destroying testbase $testbase

    rm -rf $testbase
else
    echo
    echo PRESERVING TESTBASE $testbase
fi


