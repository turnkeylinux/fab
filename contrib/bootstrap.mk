#!/usr/bin/make -f

ifndef FAB_PATH
$(error FAB_PATH not defined - needed for default paths)
endif

ifndef RELEASE
$(warning RELEASE not defined - default paths such as POOL may break)
endif

# default locations
POOL ?= $(FAB_PATH)/pools/$(RELEASE)
BOOTSTRAP_LIBEXEC ?= /turnkey/private/fab/contrib/bootstrap

all: $(RELEASE)

clean:
	-rm -rf $(RELEASE) $(RELEASE).spec
	-rm -rf base.spec required.spec $(RELEASE).repo

required.spec: plan/required
	fab-plan-resolve --output=$@ --pool=$(POOL) plan/required

base.spec: plan/base required.spec
	fab-plan-resolve --output=$@.tmp --pool=$(POOL) plan/base
	$(BOOTSTRAP_LIBEXEC)/exclude_spec.py $@.tmp required.spec > $@
	rm -f $@.tmp

$(RELEASE).spec: required.spec base.spec
	echo "# REQUIRED" > $@
	cat required.spec >> $@

	echo "# BASE" >> $@
	cat base.spec >> $@

$(RELEASE).repo: $(RELEASE).spec
	mkdir -p $@/pool/main
	POOL_DIR=$(POOL) pool-get -s -t -i $(RELEASE).spec $@/pool/main

	$(BOOTSTRAP_LIBEXEC)/repo_index.sh $(RELEASE) main $@
	$(BOOTSTRAP_LIBEXEC)/repo_release.sh $(RELEASE) main `pwd`/$@

$(RELEASE): $(RELEASE).repo $(RELEASE).spec
	$(BOOTSTRAP_LIBEXEC)/bootstrap_spec.py $@ $@.spec `pwd`/$@.repo

	rm -rf $@/var/cache/apt/archives/*.deb
	echo "do_initrd = Yes" > $@/etc/kernel-img.conf

.PHONY: clean

