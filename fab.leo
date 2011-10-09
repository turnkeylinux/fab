<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet ekr_test?>
<leo_file>
<leo_header file_format="2" tnodes="0" max_tnode_index="0" clone_windows="0"/>
<globals body_outline_ratio="0.277583187391">
	<global_window_position top="0" left="5" height="709" width="1142"/>
	<global_log_window_position top="0" left="0" height="0" width="0"/>
</globals>
<preferences/>
<find_panel_settings/>
<vnodes>
<v t="zaril.20110904173229" a="E"><vh>Project</vh>
<v t="loni.20111001190214" a="E"><vh>documentation</vh>
<v t="loni.20111001190214.1"><vh>initial release</vh></v>
<v t="loni.20111101195055" a="E"><vh>notes on fabrication setup</vh>
<v t="loni.20111101202620"><vh>apps</vh></v>
<v t="loni.20111101202620.1"><vh>configuration files</vh></v>
<v t="loni.20111101204604"><vh>apt-proxy</vh></v>
</v>
</v>
<v t="loni.20111001190214.2" a="E"><vh>development log</vh>
<v t="loni.20111001190214.3"><vh>v0.5 - initial release</vh>
<v t="zaril.20110904173337"><vh>design</vh>
<v t="zaril.20110904173337.1"><vh>brainstorming</vh></v>
<v t="zaril.20110904173337.3"><vh>terminology</vh></v>
<v t="zaril.20110904173519"><vh>high-level sketch</vh></v>
<v t="zaril.20110904173337.4"><vh>cli syntax + psuedo-logic</vh>
<v t="loni.20110911164714"><vh>fab-cpp</vh></v>
<v t="loni.20110911164714.1"><vh>fab-plan-resolve</vh>
<v t="loni.20110911164714"><vh>fab-cpp</vh></v>
</v>
<v t="loni.20110911164714.2"><vh>fab-spec-install</vh></v>
<v t="loni.20110911164714.3"><vh>fab-apply-removelist</vh></v>
<v t="loni.20110910191100.1"><vh>fab-apply-overlay</vh></v>
<v t="loni.20110911164714.5"><vh>fab-plan-lint</vh></v>
</v>
<v t="loni.20110910182617"><vh>exemplary make flow</vh>
<v t="loni.20110910182756"><vh>bootstrap</vh></v>
<v t="loni.20110910182756.1"><vh>root.spec</vh>
<v t="loni.20110911164714.1" a="E"><vh>fab-plan-resolve</vh>
<v t="loni.20110911164714"><vh>fab-cpp</vh></v>
</v>
</v>
<v t="loni.20110910182756.2"><vh>root.build</vh>
<v t="loni.20110911164714.2"><vh>fab-spec-install</vh></v>
</v>
<v t="loni.20110910182756.3"><vh>root.patched</vh>
<v t="loni.20110911164714.3"><vh>fab-apply-removelist</vh></v>
<v t="loni.20110910191100.1"><vh>fab-apply-overlay</vh></v>
</v>
<v t="loni.20110910182756.4"><vh>cdroot</vh>
<v t="loni.20110910191100.1"><vh>fab-apply-overlay</vh></v>
</v>
<v t="loni.20110910182756.5"><vh>product.iso</vh></v>
</v>
</v>
<v t="zaril.20110904181421"><vh>implementation</vh>
<v t="zaril.20110904173337.5"><vh>design exercise: port backstage to fab redesign</vh>
<v t="zaril.20110904173337.6"><vh>explore make</vh>
<v t="zaril.20110904173337.7"><vh>test: directory targets</vh></v>
</v>
</v>
<v t="loni.20110911180234"><vh>fab-cpp</vh>
<v t="loni.20110912121610"><vh>weird: s/linux/1/</vh></v>
</v>
<v t="loni.20110912123550"><vh>fab-plan-resolve</vh>
<v t="loni.20110916154247"><vh>issue: provides/virtual</vh></v>
</v>
<v t="loni.20110917153918"><vh>fab-spec-install</vh>
<v t="loni.20110917232324"><vh>mass install</vh></v>
</v>
<v t="loni.20110919154516"><vh>fab-apply-removelist</vh></v>
<v t="loni.20110920142423"><vh>fab-apply-overlay</vh></v>
<v t="loni.20110920150432"><vh>fab-chroot</vh></v>
<v t="loni.20110920175636"><vh>old vs. new plans</vh>
<v t="loni.20110920183538"><vh>notes</vh></v>
</v>
<v t="loni.20110923145602"><vh>kernel image install anomaly</vh></v>
<v t="loni.20110928121323"><vh>optimize makefile with deck</vh></v>
</v>
</v>
<v t="loni.20111009174710" a="E"><vh>unreleased</vh>
<v t="loni.20111009174710.1"><vh>plan-resolve include bootstrap</vh></v>
<v t="loni.20111010161023"><vh>plan-resolve - interactive calculation</vh></v>
<v t="loni.20111010171200"><vh>caching</vh></v>
<v t="loni.20111121155941" a="E"><vh>optimizations</vh>
<v t="loni.20111121155941.1"><vh>spec-get</vh></v>
<v t="loni.20111121155941.2" a="TV"><vh>plan-resolve</vh></v>
</v>
</v>
<v t="loni.20110928132411"><vh>TODO</vh></v>
</v>
</v>
</vnodes>
<tnodes>
<t tx="loni.20110910182617"></t>
<t tx="loni.20110910182756">rm -rf bootstrap
rm -rf bootstrap.spec
cp -a /turnkey/fab/bootstraps/rocky bootstrap
cp -a /turnkey/fab/bootstraps/rocky.spec bootstrap.spec

#notes
idea:
    * use oldfab to create drop in bootstrap

This will be added to the actual bootstrap
# The linux-image package asks interactively for initial ramdisk
# creation. Therefore, we preconfigure /etc/kernel-img.conf
echo "do_initrd = Yes" &gt; ${FABPROD}/chroot/etc/kernel-img.conf

fab/bootstraps/rocky/
        cd projects/oldfab/bin
        ./10initialize
        ./15bootstrap rocky
        cp -a /turnkey/fabarea/products/chroot/* /turnkey/fab/bootstrap/rocky/

fab/bootstraps/rocky.list
        cd projects/oldfab/bin
        ./command "dpkg -l" &gt; /turnkey/fab/bootstraps/rocky.list

fab/bootstraps/rocky.spec
        cd /turnkey/fab/bootstraps
        cat rocky.list | awk '{print $2"="$3}' &gt; rocky.spec


</t>
<t tx="loni.20110910182756.1">fab-plan-resolve /turnkey/fab/pools/rocky plan/main bootstrap &gt; root.spec


# notes
fab-plan-resolve [ -options ] &lt;pool&gt; &lt;plan&gt; [ /path/to/bootstrap ]


package=version

a spec := a set of (package name, package version) tuples
    a spec is created from a plan against a specific pool
        the same plan will generate different specs against different pools
        
- parse plan for packages
- create set construct of packages=version tuples for all packages, and their deps recursively
  by querying the pool

deps?
    in order to create the root.spec, the product plan is resolved against a pool
    resolving requires getting the version and dependencies of packages, recursively
    Q: how do we get the version and deps of packages? (problem being deps)
    
    alternatives:
        patch pool-list to have -depends option
            not good option, its not pools objective to get that info
            
        generate an index on the pool, an parse it
            directly indexing the pool is not an actual option, we would have to follow $pool/.pool/stocks
            and will only get the binary deps, not the sources
            
        pool-get all packages into a temp directory, index temp, parse the index and repeat
            kludgy...
            
        pool-get each package, extract and parse control file, do the same for each dep, continue...
            IDEA: we could use the outdir to optimize the root.build, but
                  pre-mature optimization is the root of all evil
                  and besides, pool-get shouldn't be expensive, its just a hardlink
        
Q: what is bootstrap for? we have the spec anyway?
   HYPO: plan packages depend on packages installed in the bootstrap, so we dont need to get them again...
   
Q: should the root.spec include packages already installed in the bootstrap?
   ie. should the spec be dependent on the bootstrap?
A: the root.spec should _NOT_ include bootstrap packages, together the bootstrap.spec and root.spec could be used to (almost) reasemble a product.

</t>
<t tx="loni.20110910182756.2">rm -rf root.build
cp -a bootstrap root.build
fab-spec-install /turnkey/fab/pools/rocky root.spec root.build

</t>
<t tx="loni.20110910182756.3">rm -rf root.patched
cp -a root.build root.patched
fab-apply-removelist removelist root.patched
fab-apply-overlay overlay root.patched



reminder for removelist:
    post removal: in-chroot /etc/cron.daily/slocate
    
    </t>
<t tx="loni.20110910182756.4">rm -rf cdroot
cp -a /turnkey/fab/cdroots/bootsplash cdroot
fab-apply-overlay cdroot.overlay cdroot
cp root.patched/usr/lib/syslinux/isolinux.bin cdroot/isolinux
cp root.patched/boot/vmlinuz-* cdroot/casper/vmlinuz
cp root.patched/boot/initrd.img-* cdroot/casper/initrd.gz
mksquashfs root.patched cdroot/casper/filesystem.squashfs

</t>
<t tx="loni.20110910182756.5">mkisofs -o product.iso -r -J -l \
                -V backstage \
                -b isolinux/isolinux.bin \
                -c isolinux/boot.cat \
                -no-emul-boot \
                -boot-load-size 4 \
                -boot-info-table cdroot/
</t>
<t tx="loni.20110910191100.1">* fab-apply-overlay &lt;overlay&gt; &lt;path&gt;
copy &lt;overlay&gt; over &lt;path&gt;
</t>
<t tx="loni.20110911164714">* fab-cpp &lt;plan&gt; # Internal command
pre-process a plan (light wrapper around cpp)

&lt;plan&gt; := /path/to/plan | -
    if `-' read plan from stdin

options
    -D
    -I
    (passed on to CPP)

logic
    add FAB_PLAN_INCLUDE_PATH to includes
    create list of options from our cli arguments
    executes cpp, passing list options directly</t>
<t tx="loni.20110911164714.1">* fab-plan-resolve [ -options ] &lt;pool&gt; &lt;plan&gt; [ /path/to/bootstrap ]
resolves a plan into a spec that uses the latest packages from a given pool

&lt;pool&gt; := relative/path | /absolute/path
    if relative/path, pool is looked up in FAB_POOL_PATH

&lt;plan&gt; := /path/to/plan | -
    if `-' read plan from stdin

environment variables
    FAB_TMPDIR env var
        defaults to TMPDIR or /var/tmp if not set

    FAB_POOL_PATH               lookup paths for a relative pool path
        e.g.,
            FAB_POOL_PATH=/turnkey/fab/pools

options
    -o path/to/spec-output
        by default we print spec to stdout

    [ fab-cpp options ]
        allows arbitrary CPP definitions which effect plan preprocessing

logic
    release_name = pool_name unless set explicitly
    preprocess plan
        -DRELEASE_NAME=...

    filter out all comments
    calculate package set from plan
        add packages that don't start with !
        remove packages that start with !
            if package doesn't exist in set, ignore

    print ### from plan
    for each package in plan:
        skip if package already handled

        get_package_spec():
            get package from pool
                raise exception if we can't
            extract deps and version 
            for each package in deps:
                skip if package already handled
                get_package_spec(package)

            print package=version
        
    if bootstrap argument
        print ### from bootstrap
        calculate bootstrap plan (dpkg -l)
        for each package:
            skip if package already handled
            get package from pool
                raise exception if we can't
            extract version of package

            print package=version</t>
<t tx="loni.20110911164714.2">* fab-spec-install &lt;pool&gt; &lt;spec&gt; &lt;chroot&gt;
gets packages from the &lt;pool&gt; according to the &lt;spec&gt; and installs them into the &lt;chroot&gt;

environment variables
    FAB_POOL_PATH               lookup paths for a relative pool path
        e.g.,
            FAB_POOL_PATH=/turnkey/fab/pools

&lt;pool&gt; := relative/path | /absolute/path
    if relative/path, pool is looked up in FAB_POOL_PATH

&lt;spec&gt; := /path/to/spec | -
    if spec is `-' reads spec in from stdin

logic
    mount required virtual filesystems in chroot
        /proc /dev/pts

    copies packages according to spec from the pool to chroot 
        raises exception on error (e.g., if we can't get a package according to the spec)

    installs all the packages with dpkg
        raises exception if dpkg fails (e.g., missing dependency, configure failure, etc.)

    prints dpkg output to stdout

    unmount virtual filesystems in chroot (if we mounted them ourselves)</t>
<t tx="loni.20110911164714.3">* fab-apply-removelist &lt;remove-list&gt; &lt;path&gt;
remove files and directories as specified by &lt;removelist&gt; from &lt;path&gt;</t>
<t tx="loni.20110911164714.5">* fab-plan-lint [ -options ] &lt;pool&gt; &lt;plan&gt; [ ... ]
pretty print each package in the plan with its short description as a comment

&lt;pool&gt; := relative/path | /absolute/path
    if relative/path, pool is looked up in FAB_POOL_PATH

&lt;plan&gt; := /path/to/plan | -
    if `-' read plan from stdin

environment variables
    FAB_TMPDIR env var
        defaults to TMPDIR or /var/tmp if not set

    FAB_POOL_PATH               lookup paths for a relative pool path
        e.g.,
            FAB_POOL_PATH=/turnkey/fab/pools

options
    -i          edit plan in-place

logic
    if -i, redirect print output to temporary file

    parse plan into lines
    for each line:
        if only comment / new line, print and skip to the next line
        parse package name
        get package from pool into TMPDIR
        raise exception if get fails
        extract short description
        print package name + "#" + short description
    
    if -i, copy temporary file over plan</t>
<t tx="loni.20110911180234">fab-cpp is an internal command, called by fab-plan-resolve

-----------------------/
fab-cpp [-options] &lt;plan&gt;

Pre-process a plan (internal command)

Arguments:
  &lt;plan&gt;                path to read plan from (- for stdin)
  
Options:
  --cpp=                 options to pass directly to the C Preprocessor

-----------------------/

cpp -I&lt;FAB_PLAN_INCLUDE_PATH&gt; &lt;plan&gt;
    eg.
    cpp -I/turnkey/fab/common-plans plan/main
    
Q: how do i pass the plan i read from stdin to CPP?
A: cpp will read from stdin if '-' is specified
    note: if no infile not '-' is specifed, stdin is specified as default
    
IDEA:
    read in plan, whether file or stdin
    pass "plan contents" to cpp on stdin
    eg.
        cat plan/main | cpp -I/turnkey/fab/common-plans
        
problem: local includes aren't found, we have to give the path
    cat plan/main | cpp -I/turnkey/fab/common-plans -Iplan
    
Q: should fab-cpp have options, such as -I, -D, etc?
    we could have multiple include options, how would we handle that?
    
    IDEA: have option called --cpp="" to pass options directly to cpp


&lt;plan&gt; | cpp -I&lt;FAB_PLAN_INCLUDE_PATH&gt; &lt;CPP_EXTRA_OPTIONS&gt;


</t>
<t tx="loni.20110912121610">the word "linux" is being replaced by the number 1 with a space:
    s/linux/1 /

    $ echo linux-test | cpp
    # 1 "&lt;stdin&gt;"
    # 1 "&lt;built-in&gt;"
    # 1 "&lt;command line&gt;"
    # 1 "&lt;stdin&gt;"
    1 -test


It seems "linux" is a macro, with a definition of 1.

Solution: redefine the macro

    $ echo linux-test | cpp -D linux=linux
    # 1 "&lt;stdin&gt;"
    # 1 "&lt;built-in&gt;"
    # 1 "&lt;command line&gt;"
    &lt;command line&gt;:1:1: warning: "linux" redefined
    &lt;built-in&gt;: warning: this is the location of the previous definition
    # 1 "&lt;stdin&gt;"
    linux-test


Better Solution: undefine the macro

    $ echo linux-test | cpp -U linux
    # 1 "&lt;stdin&gt;"
    # 1 "&lt;built-in&gt;"
    # 1 "&lt;command line&gt;"
    # 1 "&lt;stdin&gt;"
    linux-test

Q: should we add this to fab-cpp?
A: no, it should be added by the user of fab-cpp, along with any other cpp options he wishes
</t>
<t tx="loni.20110912123550">fab-plan-resolve [ -options ] &lt;pool&gt; &lt;plan&gt; [bootstrap.spec]

Resolve plan into spec using the latest packages from a given pool

Arguments:
  &lt;pool&gt;                Relative or absolute pool path
                        If relative, pool path is looked up in FAB_POOL_PATH
  &lt;plan&gt;                Path to read plan from (- for stdin)
  bootstrap.spec        Path to spec of packages to not be included in root.spec
  
Options:
  --output=             Path to spec-output (default is stdout)
  --cpp=                Arbitrary CPP definitions to effect plan preprocessing


-----------------------/

bootstrap
---------
i don't know how we will be creating the bootstrap, so currently i 
am using a dropin created with oldfab.

to get around the need for root privs to get a list of packages in the bootstrap (dpkg -l), 
or getting the list from a bootstrap source list (not decided upon yet), i have also created
a list manually created with dpkg -l.

i then turned the list into a bootstrap.spec, which will be used by resolve-plan
root.spec will _not_ include packages in the bootstrap.spec





TODO:
    support bootstrap argument
    update Makefile
    
    clean up code
    
    move onto fab-spec-install...
    

logic
    release_name = pool_name unless set explicitly
    preprocess plan
        -DRELEASE_NAME=...

    filter out all comments
    calculate package set from plan
        add packages that don't start with !
        remove packages that start with !
            if package doesn't exist in set, ignore

    print ### from plan
    for each package in plan:
        skip if package already handled

        get_package_spec():
            get package from pool
                raise exception if we can't
            extract deps and version 
            for each package in deps:
                skip if package already handled
                get_package_spec(package)

            print package=version
        
    if bootstrap argument
        print ### from bootstrap
        calculate bootstrap plan (dpkg -l)
        for each package:
            skip if package already handled
            get package from pool
                raise exception if we can't
            extract version of package

            print package=version</t>
<t tx="loni.20110916154247">
pool-get can't/doesn't get a package requested if the package name is provided by a package
eg. perlapi-5.8.7 (dep via dep of casper)
    is provided by perl-base

possible solutions:
    * fork the packages that depend on "provided" packages
    * add functionality to pool
    * add functionality to fab
    * add a virtual package
    * add a meta-package to the package pool


we can't "get_package_spec" of a virtual package
eg. libapt-pkg-libc6.4-6-3.53 (dep of apt-utils)

</t>
<t tx="loni.20110917153918">fab-spec-install &lt;spec&gt; &lt;pool&gt; &lt;chroot&gt;

Installs packages from given pool in chroot according to the spec

Arguments:
  &lt;spec&gt;                Path to read spec from (- for stdin)
  &lt;pool&gt;                Relative or absolute pool path
                        If relative, pool path is looked up in FAB_POOL_PATH
  &lt;chroot&gt;              Path to chroot


-----------------------/

rm -rf root.build
cp -a bootstrap root.build
fab-spec-install /turnkey/fab/pools/rocky root.spec root.build


logic
    mount required virtual filesystems in chroot
        /proc /dev/pts

    copies packages according to spec from the pool to chroot 
        raises exception on error (e.g., if we can't get a package according to the spec)

    installs all the packages with dpkg
        raises exception if dpkg fails (e.g., missing dependency, configure failure, etc.)

    prints dpkg output to stdout

    unmount virtual filesystems in chroot (if we mounted them ourselves)
    
oldfab related notes
    20mountpoints
        mount proc-chroot ${FABPROD}/chroot/proc -t proc
        mount devpts-chroot ${FABPROD}/chroot/dev/pts -t devpts
        
    21finalize-bootstrap (maybe this should be in the bootstrap already?)
        echo "do_initrd = Yes" &gt; ${FABPROD}/chroot/etc/kernel-img.conf
    
    install-packages
        create fake start-stop daemon
        inchroot
            chroot ${FABPROD}/chroot /usr/bin/env -i HOME=/root TERM=${TERM} \
                LC_ALL=C PATH=/usr/sbin:/usr/bin:/sbin:/bin \
                DEBIAN_PRIORITY=critical ${1}
        replace fake start-stop daemon with real
    
        note: remove debs
    
    35umountpoints
        umount -f devpts-chroot
        umount -f proc-chroot
        

</t>
<t tx="loni.20110917232324">mass installing via dpkg is failing
    this is due to dpkg not preconfiguring what packages to install in what 
    order, and generating tons of errors
    
    default max errors is 50, i gradually increased the max error amount upto 
    100,000 with --abort-after, but it is still failing... - but different error
    
    we now have a dependency problem.
    
HYPO: bug in plan-resolve?
    Test: setup apt and try the install using apt-get
    Result: yes, i was missing dependencies

manually setup apt
    cd root.build
    mkdir -p dists/rocky/fab/binary-i386
    apt-ftparchive packages fab/ | gzip -9 &gt; dists/rocky/fab/binary-i386/Packages.gz
    echo "deb file:/// rocky fab" &gt; etc/apt/sources.list

    chroot into root.build
        apt-get update
        PKGS=""; for p in $(apt-cache pkgnames); do PKGS="$PKGS $p"; done
        apt-get install $PGKS
    
    IDEA: put the packages directly into /var/cache/apt/archives/

The following packages have unmet dependencies:
  aspell-en: Depends: aspell (&gt;= 0.60.3-2) but it is not installable
  build-essential: Depends: gcc (&gt;= 4:4.1.1) but it is not installable
                   Depends: make but it is not installable
  defoma: Depends: file but it is not installable
  dpkg-dev: Depends: make but it is not installable
  firefox: Depends: fontconfig but it is not installable
  g++: Depends: gcc (&gt;= 4:4.1.2-1ubuntu1) but it is not installable
       Depends: gcc-4.1 (&gt;= 4.1.2) but it is not installable
  g++-4.1: Depends: gcc-4.1 (= 4.1.2-0ubuntu4) but it is not installable
  hal: Depends: dbus (&gt;= 0.60-1) but it is not installable
  liblaunchpad-integration0: Depends: launchpad-integration but it is not installable
  libpango1.0-common: Depends: fontconfig (&gt;= 2.1.91) but it is not installable
  libqt3-mt: Depends: fontconfig but it is not installable
  xbase-clients: Depends: xrandr but it is not installable
                 Depends: bitmap but it is not installable
                 Depends: ico but it is not installable
                 Depends: xf86dga but it is not installable
E: Broken packages


For some reason, the root.spec doesn't have all the packages we need....

Found the issue: bug in the resolve code
    package "abc" would not be added to the package set if a package containing "abc" was already in the set

-----------------

dpkg can't seem to handle figuring out which packages to install in what order.
it keeps on breaking...

Errors were encountered while processing:
 fab/xutils-dev_7.1.ds-6ubuntu1_i386.deb
 fab/libxft2_2.1.12-1_i386.deb
 fab/libxfixes3_4.0.3-1_i386.deb
 fab/libx11-6_1.1.1-1ubuntu3_i386.deb
 fab/xbitmaps_1.0.1-0ubuntu2_all.deb
 fab/libxt6_1.0.5-1_i386.deb
 fab/x11-common_7.2-0ubuntu11_i386.deb
 fab/libdmx1_1.0.2-2build1_i386.deb
 fab/libx11-data_1.1.1-1ubuntu3_all.deb
 fab/xserver-xorg_7.2-0ubuntu11_all.deb

we have to add some intellegence ontop of dpkg.
manually hunting down which debs to install first, i am able to complete the installation 
    Q: why does dpkg fail...?

    Note: fixing dependencies with dpkg
            dpkg -i --force-depends packages...
            dpkg --configure --pending
            &lt;repeat until no errors&gt;
    
    This is a horrible solution, why kludge fixing dependency problems if we can just install packages correctly?

options:
    * figure out the order ourselves
        apt-python  - still have to implement apt related stuff
        scratch     - reinvent the wheel
        
    * leverage a dpkg frontend
        dselect     - interactive ui
        aptitude    - interactive ui
        apt
            - seems to be the least worse option (manual test successful)

leveraging apt will definately work, and wont take too long
downside is that we will depend on apt

at a later stage, we can develop a solution to figure out the the order, and use dpkg


* apt implementation: refer to chanko
    * pool-get outdir=${root.build}/var/cache/apt/archives
    * index outdir and save directly to lists/_dists_local_debs_binary-i386_Packages
    * create sources.list
    * apt-get update
    * get list of packages to install
        * parse the spec
        * apt-cache pkgnames
    * apt-get install $PGKS


    




</t>
<t tx="loni.20110919154516">fab-apply-removelist &lt;removelist&gt; &lt;path&gt;

Removes files and folders as specified by removelist from the path

Arguments:
  &lt;removelist&gt;          Path to read removelist from (- for stdin)
                        Entries may be negated by prefixing a !
  &lt;path&gt;                Path containing removelist entries (ie. chroot)


-----------------------/


fab-apply-removelist removelist root.patched
   

example removelist contents
    /usr/share/locale/
    !/usr/share/locale/en_GB/
    
the above would remove locale/* except for locale/en_GB
note: the files removed are not deleted, but moved out of the path (ie. the chroot)


</t>
<t tx="loni.20110920142423">fab-apply-overlay &lt;overlay&gt; &lt;path&gt;

Applies overlay ontop of path

Arguments:
  &lt;overlay&gt;             Path to overlay
  &lt;path&gt;                Path apply overlay ontop of (ie. chroot)


-----------------------/


fab-apply-overlay overlay root.patched

from oldfab blueprint overrides:

if [ -d ${BP_DIR}/overrides ]; then
        cp -a ${BP_DIR}/overrides/* ${FABPROD}/chroot/
fi


Note: when using deck, just add it as another layer?
      have option?

</t>
<t tx="loni.20110920150432">fab-chroot &lt;chroot&gt; [command]

Executes command in chroot

Arguments:
  &lt;chroot&gt;              Path to chroot
  command               Command to execute in chroot
                        If no command is specified, an interactive shell is assumed
                        
----------------------------/

</t>
<t tx="loni.20110920175636">the following diff was done on rocky backstage, after "recommended packages" where removed

buildingblocks vs. common-plans
-------------------------------
only in buildingblocks
    fvwm
    feh
    hal
    nano
    apt-utils
    debconf-utils
    ucf
    fcron
    slocate

only in common-plans
    kbd


blueprint vs. plan
------------------
only in buildingblocks
    kbd
    
only in plan
    fvwm
    feh
    fcron
    apt-utils
    debconf-utils
    ucf
    hal
    gnupg


summary
-------
after canceling out...


only in buildingblocks
    nano
    slocate

only in plan
    gnupg (we have it in buildingblocks bootstrap, leaving it for now...)

</t>
<t tx="loni.20110920183538">remove dependencies from plans? 
    usplash
    fvwm

usplash-theme-backstage -&gt; usplash-theme-turnkey

add to console
    nano (we need a basic text editor in the console)

</t>
<t tx="loni.20110923145602">spec-install

Interactive Prompt:

If /lib/modules/2.6.20-15-386/kernel belongs to old install
of linux-image-2.6.20-15-386, then this is your last chance to
abort the installation of this kernel image (nothing has been 
changed yet).

If you know what you are doing, and if you feel that this image
should be installed despite this anomaly, Please answer n to
the question.

Otherwise, I suggest you move /lib/modules/2.6.20-15-386/kernel
out of the way, perhaps to
/lib/modules/2.6.20-15-386.kernel.old or something, and then
try re-installing this image.

Stop install since the kernel-image is already installed?

Yes/No ??


Q: Offending package: ?
    linux-image-2.6.20-15-386

    Nope: thats where we get the error, but the package aufs-modules-2.6.20-15-386
    was the culprit, it was unpacked before linux-image*

IDEA: install the linux-image* packages first before any others
</t>
<t tx="loni.20110928121323">* deck uses useraufs, useraufs errors out saying it can't be run by root

Q: should we remove the dependency of root, and either fakechroot or suid fab?
A: no, fakechroot is a deadend, and fab shouldn't be suid
   useraufs can be configured to allow root
   
   /etc/useraufs.conf
      allow_user root
      allow_dir /turnkey/fab

Problem: deck errors out saying that it can't be run by root
GOTCHA: useraufs was installed to usr/bin, and the updated version is installed to /usr/local/bin - deck was using the older version, while manual testing was using the new version - damn waste of time...


IDEA: maybe deck bootstrap/rocky directly to root.build ?


Q: why are we decking bootstrap/rocky to bootstrap, then bootstrap to root.build?
    we aren't making any changes to the bootstrap
    
    maybe do the deck directly
    maybe create the bootstrap.spec from the bootstrap itself?
        why? we create it before creating the bootstrap...
        
        </t>
<t tx="loni.20110928132411">plan-resolve
    depends on version checking
    provides / virtual packages

product recipe := a light bundle of data from which a product can be recreated from source
    a product recipe is created during the creation of a new product
        by recording the outputs of the build
            bootstrap spec
            root spec
            root patch
            product format configuration

bootstrap
    * minimize plans
    * leverage fab-plan-resolving of base to add packages to required
    * remove debootstrap dependency

apt -&gt; dpkg
    * use dpkg instead of apt when installing packages
    * ideas:
            * debootstrap scripts
            * spec analysis code

spec-analysis
    * same idea as oldfab/package-analysis
    


</t>
<t tx="loni.20111001190214"></t>
<t tx="loni.20111001190214.1">FAB: product fabrication framework

This version of Fab is actually the second generation framework, the first being referred to as oldfab.

The word "Fab" originates from the microelectronics industry. A fab, or fabrication plant is a factory where devices (eg. integrated circuits) are manufactured for one of more customers. A fab is semantically connected to the most cutting edge technological factories in existence (Silicon chip foundries) - hence the relationship to TurnKey ;)

A fab is a very tightly controlled environment (clean room), but instead of keeping out physical impurities (e.g., dust and dirt), the turnkey Fab is used in fabricating systems while tightly controlling "logical" impurities (e.g., security threats, malware, etc.)

These release notes only contain a high-level overview, please refer to the design notes for detailed information, and help from the commands themeselves.

OVERVIEW
--------
The fab provides 'toolchain' utilities, which allows us to build products and collaborate on them using the same workflow and tools used on software projects.

Building is performed per-product, each in its own directory. We leverage 'make' to implement the 'build pipeline', git and covin for revision control and collaboration.

The output of a product is the product itself, and a recipe (very small footprint compared to the product) which can be use to automatically reproduce the product bit for bit.
                   

TERMINOLOGY
-----------

product: the final product used by the end-user
    the product is generated by formatting the "patched root"

root.patched: the chroot'able root filesystem of a product
    patched manually or automatically
    can be re-created automatically by applying the root patch as an overlay to `the root'

root.build: the chroot'able root filesystem of a product
    built by applying the "root.spec" on the bootstrap

bootstrap: the minimal chroot'able filesystem used to bootstrap the root
    built from a "bootstrap.spec"

spec: a set of (package name, package version tuples)
    a spec is created from a plan against a specific pool
    the same plan will generate different specs against different pools

plan: set of package names
    root plan
        the recursable plan from which the root.spec is created
        recursable means we lookup the dependencies of listed packages recursively
    
    bootstrap plan
        the non-recursable plan from which we create the bootstrap spec
        non-recursable means no recursion of the plan (this is planned to change)

CLI
---

Fab has 4 basic commands,
    plan-resolve        Resolve plan into spec using latest packages from pool
    spec-install        Install packages into chroot according to spec
    apply-removelist    Remove files and folders according to removelist
    apply-overlay       Apply overlay ontop of given path

4 internal/advanced commands,
    cpp                 Pre-process a plan
    chroot              Executes command in chroot
    chroot-umount       Umount chroot virtual filesystems if mounted
    spec-get            Get packages according to spec
        
and can be configured via 3 environment variables,
    FAB_PLAN_INCLUDE_PATH   Global include path for plan preprocessing
    FAB_POOL_PATH           Lookup path for a relative pool path
    FAB_TMPDIR              Temporary storage (defaults to /var/tmp)



</t>
<t tx="loni.20111001190214.2"></t>
<t tx="loni.20111001190214.3"></t>
<t tx="loni.20111009174710"></t>
<t tx="loni.20111009174710.1">rational:
    the product plan might include newer package versions of those already installed in the bootstrap
    we might be getting rid of the "bootstrap" down the line
    the root.spec should include every package in the product.


Syntax: plan-resolve [-options] &lt;plan&gt; &lt;pool&gt;
Resolve plan into spec using latest packages from pool

Arguments:
  &lt;plan&gt;            Path to read plan from (- for stdin)
  &lt;pool&gt;            Relative or absolute pool path
                    If relative, pool path is looked up in FAB_POOL_PATH

Options:
  --exclude=        Path to spec of packages not to be resolved
  --output=         Path to spec-output (default is stdout)
  --chroot=         Path to chroot installed with packages to append to &lt;plan&gt;


Q: how do i get a list of only package names installed in a chroot?
A: dpkg-query --show -f="${Package}\n"

</t>
<t tx="loni.20111010161023">current algorithm: global calculation
    create set of 'yes' and 'no', then subtracts
    
    pro: allows for declaring "retractions" anywhere in the plan, and them sticking
    con: does not allow for inheritance behaviour


new algorithm: interative calculation
    work on one set, add and remove to/from it
    
    pro: allows for redeclaring a package that has been retracted
         useful for modifying included plan segments
    con: retractions will only take effect depending on their ordering
    
IDEA:
    issue warnings if attempting to "retract" a package that is not declared
    
</t>
<t tx="loni.20111010171200">Q: what is taking the most amount of time?
    getting packages from pool?
        from my tests, it takes approx. 0.6sec per package
        
    peeking into packages to get their version and dependencies
        minimalistic. with caching we could maybe shave off a fraction of a second.
        the bottlenect is pool-get at the moment.


    </t>
<t tx="loni.20111101195055">There are several apps involved in the fabrication process, each has its own job, and does it well. Each app is well documented, and will not be repeated here.

These notes are an attempt to explain how they all come together to form the fabrication infrastructure, and provide a high-level overview on how they use each other.

Everything is configurable.
The below notes are exemplary, and describe rocky/backstage (release/product).

#create fabrication folders
mkdir -p /turnkey/fab/products
mkdir -p /turnkey/fab/buildroots
mkdir -p /turnkey/fab/deckdebuilds
mkdir -p /turnkey/fab/pools/rocky

#register projects from stash
cd stashes/alon
covin-register-dest /turnkey/fab/bootstraps
covin-register-dest /turnkey/fab/cdroots
covin-register-dest /turnkey/fab/common-plans
covin-register-dest /turnkey/fab/pools/rocky/rocky.chanko
covin-register-dest /turnkey/fab/products/backstage

#setup pool (and subpool)
    initialize /turnkey/fab/pools/rocky/rocky.chanko as a pool and register arena
    initialize /turnkey/fab/pools/rocky as pool, and register stocks
        register rocky.chanko as a stock (subpool)

#update configuration files
    useraufs.conf
    deckdebuild.conf

#create the bootstrap
    cd /turnkey/fab/bootstrap
    make
    
#setup buildroot
    cp -a /turnkey/fab/bootstraps/rocky /turnkey/fab/buildroots/
    if using apt-proxy (recommended)
        configure on host
        point buildroots/rocky's sources.list to use proxy (127.0.0.1:9999)
    chroot buildroots/rocky
        apt-get update
        apt-get install fakeroot build-essetial debhelper cdbs dpatch autotools-dev

#fab a product
    cd /turnkey/fab/products/backstage
    make


</t>
<t tx="loni.20111101202620">private depends:
    fab
    pool
    deck
    deckdebuild
    useraufs
    verseek

private recommends:
    chanko
    sumo

world depends:
    pbuilder                        # deckdebuild
    debootstrap (+ rocky script)    # used to create bootstrap

world recommends:
    apt-proxy

</t>
<t tx="loni.20111101202620.1">/etc/useraufs.conf
    allow_user loni         # replace with your username
    allow_user root
    allow_dir /turnkey/fab
    
/etc/deckdebuild.conf
    vardir /turnkey/fab/deckdebuilds
</t>
<t tx="loni.20111101204604">/etc/apt-proxy/apt-proxy-v2.conf
	address = 127.0.0.1
	min_refresh_delay = 86400s # how often we refresh Packages/Sources (instead of 1s)
	max_versions = 10 # how many different versions of packages to cache

rocky $ cat /etc/apt/sources.list

deb http://127.0.0.1:9999/ubuntu feisty main universe
deb http://127.0.0.1:9999/ubuntu feisty-backports main universe



full feisty stuff
-----------------
deb http://127.0.0.1:9999/ubuntu feisty main restricted universe multiverse
deb http://127.0.0.1:9999/ubuntu feisty-updates main restricted
deb http://127.0.0.1:9999/ubuntu feisty-security main restricted
deb http://127.0.0.1:9999/ubuntu feisty-backports main restricted

deb-src http://127.0.0.1:9999/ubuntu feisty main restricted universe multiverse
deb-src http://127.0.0.1:9999/ubuntu feisty-updates main restricted</t>
<t tx="loni.20111121155941"></t>
<t tx="loni.20111121155941.1">BEFORE
$ time fab-spec-get spec-noepochs /turnkey/fab/pools/rocky packages/
real    0m27.099s
user    0m15.465s
sys     0m9.293s

AFTER
$ time ../fab-spec-get spec /turnkey/fab/pools/rocky packages/
real    0m0.206s
user    0m0.136s
sys     0m0.060s


140 times faster!!!

OPTIMIZATION: call pool-get with spec (instead of each package seperately)
</t>
<t tx="loni.20111121155941.2">plan-resolve (synapse, sumo, pool)

BEFORE
real    0m19.148s
user    0m11.101s
sys     0m6.764s

not executing pool-get (pretending it was already executed)
real    0m2.591s
user    0m1.156s
sys     0m0.768s

its taking a long time because pool-get each package seperately.

IDEA:
    dump the whole pool with the latest packages, then calculate the plan   
    we can further optimize by caching package dependencies, so we dont have to unpack and parse debs.
    
    getting the whole pool:

    $ time POOL_DIR=/turnkey/fab/pools/rocky pool-get tmp

    real    0m0.200s
    user    0m0.128s
    sys     0m0.060s

    the downside: we might be building packages we don't need to resolve the plan
        this can become a pain when the packages we dont need are big, and take a long time to build
        eg. kernel, firefox
        
        but, this depends on the pool stock registrations


AFTER
real    0m3.546s
user    0m1.580s
sys     0m1.112s


5.5 times faster!!!

OPTIMATION: dump all packages in pool first, then resolve the plan




plan resolve on the entire backstage plan

BEFORE
real    1m29.078s
user    0m51.559s
sys     0m32.438s


AFTER
real    0m18.576s
user    0m7.456s
sys     0m4.752s


5 times faster!!!

</t>
<t tx="zaril.20110904173229">@nocolor
</t>
<t tx="zaril.20110904173337"></t>
<t tx="zaril.20110904173337.1">* REMINDER: design principles
do simplest thing that could work
let the future take care of itself

* IDEAS
use dpkg's --root=&lt;dir&gt; option to set root
    chroots into &lt;dir&gt; in order to run installation scripts

add option to deck that only unmounts submounts?

* QUESTIONS
Q: what is the name of the system?
A:
    fab for short
    product fabrication framework
---
Q: name of subcommand that creates the spec from the plan?
A:
plan-resolve
    goes nicely with plan-lint

alternatives
    make-spec
    
    resolve
    resolve-plan
    make-spec
    create-spec
    implement-plan
    calc-spec
    compile-spec
    compile-plan
    process-plan
---

Q: name of subcommand that applies the spec to a bootstrap?
A:
spec-build
---
Q: suffix for plan files?
A: no suffix, identify plan files by context (in their own directory)
---

FUTURE

Q: what is the workflow for recreating a recipe?
---
Q: how to handle required/base bootstrapping plans?
    two separate non-recursable plans?
    eliminate the base list, stay with just the required?
        pass that to debootstrap?
</t>
<t tx="zaril.20110904173337.3">product := the final product used by the end-user
    a product is created by formatting the `patched root' according to the format configuration
        example format types (inspired by rpath)
            CDROM ISO
            network bootable PXE image
            root tarball
            vmware workstation image
            vmware ESX image
            Xen image
            Parallels image

    a product can be generated automatically in multiple forms

the patched root := the chroot'able root filesystem of a product, patched manually or automatically
    can be re-created automatically by applying the root patch as an overlay to `the root'

the root patch := an overlay recording any changed performed by manual or automatic means to `the root'
    distributed as a tarball in `the recipe'

the root := the chroot'able root filesystem of a product
    built by applying the `root spec' on the `bootstrap'

a build := a filesystem created from a `spec'
    e.g., root build, bootstrap build
    
    in the correct context, build is implied if it is dropped
        e.g., `root' means `root build'

the bootstrap := the minimal chroot'able filesystem used to bootstrap the root
    built from a bootstrap spec

a plan := a set of package names (I.e., see Python's set construct)
    plan types:
        root plan := the recursable plan from which we create the root spec
            recursable means we lookup the dependencies of listed packages recursively
        
        bootstrap plan = the non-recursable plan from which we create the bootstrap spec
            non-recursable means no recursion of the plan 
        
            due to implementation constraints may need to be separated into two parts (required, base)
                hopefully not

    plans = buildingblocks + blueprint's packages file
        building blocks term has been eliminated
        plan grouping has been implemented in a more flexible, generic way (cpp)
            a single plan (e.g., for backstage) can support multiple `releases' (sphinx, rocky)

a spec := a set of (package name, package version) tuples
    a spec is created from a plan against a specific pool
        the same plan will generate different specs against different pools

    plan types:
        root spec := the spec from which the root is built
        bootstrap spec := the spec from which the bootstrap is built
            due to implementation details, may need to be separated into two parts
                e.g., required and based (for debootstrap)
            
                preferably there could be some way simplify this into one list
        
product recipe := a light bundle of data from which a product can be recreated from source
    a product recipe is created during the creation of a new product
        by recording the outputs of the build
            bootstrap spec
            root spec
            root patch
            product format configuration</t>
<t tx="zaril.20110904173337.4">* global environment variables 
    FAB_PLAN_INCLUDE_PATH       global include path for plan preprocessing
        e.g.,
            FAB_PLAN_INCLUDE_PATH=/turnkey/fab/common-plans
        
    FAB_POOL_PATH               lookup paths for a relative pool path
        e.g.,
            FAB_POOL_PATH=/turnkey/fab/pools

    FAB_TMPDIR                  where fab utils store temporary files (defaults to TMPDIR or /var/tmp)
</t>
<t tx="zaril.20110904173337.5">REMINDER: converting buildingblocks to plan

perl -i -pe 's/^ \* //; s/==/##/g; s/\((.*?)\)/\1/g'    </t>
<t tx="zaril.20110904173337.6">* RESOURCE: info make

export FOO
	export FOO to sub-programs

override FOO = value
	ignore user-set value for FOO (I.e., passed as argument)

FOO ?= bar
	set FOO to bar only if FOO is not already set

FOO := bar
	expanded

FOO = bar
	recursively expanded

* QUESTIONS
Q: can directories be targets?
A:
    yes
    target must assume directory already exists
        rule is executed if dependencies are newer than the directory
        touch directory to update its modification time
        changing contents of existing file in directory does not change its mod time
---
Q: is there a difference between target and target/
A: yes, target/ is unreliable, use target instead
---
Q: are Makefile variables set in the environment
A: no, unless .EXPORT_ALL_VARIABLES is used, or the variable is exported

    not exported (by default)
        FOO=bar
    exported
        export FOO=bar
---
Q: how are cli variables handled differently?
A:
    variables passed on the cli seem to forcefully override the Makefile's variables

    experiment

        Makefile
            FOO = not changed
            env:
                echo $(FOO)
            
        FOO=changed make env
            not changed
    
        make env FOO=changed
            changed
---

Q: how do we access environment variables in the Makefile?
A:
    all variables in the environment are already set in the Makefile
    experiment
        Makefile
            env:
                @echo $(FOO)
    
        FOO=foo make env
    
---
Q: how do set a default value only if the variable has not yet been defined in the environment
    I.e., environment definition takes precedence over local definition
A:
    Makefile
        FOO ?= foo
    
        env:
            @echo $(FOO)
    
    FOO=bar make env
        bar

  </t>
<t tx="zaril.20110904173337.7"># echo hello &gt; file
# make clean
# make
# rm -rf foo
# make (should recreate foo.copy)

all: foo.copy

clean:
	rm -rf foo/ foo.copy/

foo: file
	mkdir -p $@
	cp $&lt; $@

foo.copy: foo
	cp -a $&lt; $@
</t>
<t tx="zaril.20110904173519">new design disintegrates fab into multiple independent layers

fab phases
    make bootstrap
        context: new bootstrap created per-release
            can be recreated at any time from bootstrap spec
    
        steps
            make bootstrap-spec # only if creating new bootstrap
                inputs: pool, bootstrap plan
    
            make bootstrap
                inputs: pool, bootstrap spec
    
    make root
        context: performed per-product
    
        steps
            make root-spec # only if creating a new root
                inputs: pool, bootstrap, root plan
    
            make root
                inputs: pool, bootstrap, root spec
    
    make root patch
        output: tarball of the overlay created
    
        more than one way to create root patch
            manually (e.g., with deck)
            automatically
                apply overrides/removes
                run hook scripts which perform arbitrary changes on the root
                    e.g., this is one way we could implement licop-like `activation'
            hybrid (automatic changes + manual changes)
            
    make product
        inputs: patched root + format configuration
        a single patched root may be formatted into multiple format types
    
product build workflow
    how its different
        new design is local, old design is global
            in the new design building is not performed in a global context
                e.g., we don't dump builds to /turnkey/fabarea
    
    we build products using the same workflow and tools used to build compiled software
        building performed per-product, each product in its own directory
        we leverage make to implement the `build pipeline'
        the build source for each product distributed via Git
        .gitignore build products
    
        standard Makefile structure (I.e., standard targets like debian/rules)
    
        decrease repetition of standard tasks via
            debhelper equivalents for the build process
            included Makefile fragments (I.e., like Debian's CDBS)
    
        outputs for each product
            the formatted product itself
            a recipe that can be used to automatically reproduce the product
                properties of the recipe
                    very small footprint compared to the product
                    accurate enough to recreate product from sources bit for bit
                                
pool design changes
    pool can now be configured to include other pools
        GOTCHA: circular dependencies need to be checked for and prevented
            when a user asks to register pool A into pool B
                list all sub-pools in pool A recursively
                if B is already included, raise an exception
                    (we can't have B can't including itself...)
        
    fab programs will not support multiple pools - will work with only one pool
        pool will be configured as an absolute path or relative path
            relative paths looked up in POOL_PATHS
                e.g.,
                    POOL_PATHS="/turnkey/pools"

        Q: how do we set which pool a program is supposed to work with?
        A: IDEAS
            command line option            

            passed to the program via an environment variable
                POOL="rocky"
    
                environment can be overridden via standard command lineoption
                    --pool rocky
                    --pool /turnkey/pools/rocky
        
        also configurable via command line option

plans
    goals: 
        support re-use of package grouping
        support per-release configuration of changes to re-usable package groupings
    
    plans leverage cpp (c pre-processor)
        grouping achieved via cpp includes
        global include paths should configurable
            #include &lt;global/path/to/plan&gt;
    
            from cli 
                -I/path/to/includable/plans
            from environment variable
                PLAN_INCLUDE_PATH
            
        local includes paths should be relative
            #include "relative/path"
            
        we can use CPP to implement global release profiles
            per-release
        
        embed release-specific ifdef statements in package groups
            ifdef triggered by release profile which is triggered by the pool name
    
    linting program adds package short description as comments
        support editing in-place or output to stdout
        works on pre-processed and non-preprocessed plans
    
    plan format
        &lt;package&gt; # this adds the package to the plan set
        !&lt;package&gt; # this removes the package (which may have been included earlier) from the plan set</t>
<t tx="zaril.20110904181421">ROADMAP
    fab-cpp    
    fab-plan-resolve
    
    bootstrap dropin
    fab-spec-install

    fab-apply-overlay

    fab-apply-removelist
    fab-plan-lint

    integrate deck support
    full logging and re-fab support from specs
    
    non-root support?
        fakeroot, fakechroot
        suid wrappers for critical tasks?

</t>
</tnodes>
</leo_file>
