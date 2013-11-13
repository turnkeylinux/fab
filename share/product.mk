#!/usr/bin/make -f
# Copyright (c) TurnKey Linux - http://www.turnkeylinux.org
#
# This file is part of Fab
#
# Fab is free software; you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by the
# Free Software Foundation; either version 3 of the License, or (at your
# option) any later version.

ifndef FAB_PATH
$(error FAB_PATH not defined - needed for default paths)
endif

ifndef RELEASE
$(error RELEASE not defined)
endif

DISTRO ?= $(shell dirname $(RELEASE))
CODENAME ?= $(shell basename $(RELEASE))

UBUNTU = $(shell [ $(DISTRO) = 'ubuntu' ] && echo 'y')
DEBIAN = $(shell [ $(DISTRO) = 'debian' ] && echo 'y')

FAB_ARCH = $(shell dpkg --print-architecture)
I386 = $(shell [ $(FAB_ARCH) = 'i386' ] && echo 'y')
AMD64 = $(shell [ $(FAB_ARCH) = 'amd64' ] && echo 'y')

ifdef FAB_POOL
FAB_POOL_PATH=$(FAB_PATH)/pools/$(CODENAME)
export FAB_POOL_PATH
endif

ifdef FAB_POOL_PATH
FAB_INSTALL_OPTS = '--no-deps'
else
ifndef FAB_APT_PROXY
$(warning FAB_POOL_PATH and FAB_APT_PROXY are not defined)
endif
endif

ifndef FAB_HTTP_PROXY
$(warning FAB_HTTP_PROXY is not defined)
endif

CONF_VARS_BUILTIN ?= FAB_ARCH FAB_HTTP_PROXY I386 AMD64 RELEASE DISTRO CODENAME DEBIAN UBUNTU KERNEL DEBUG CHROOT_ONLY

define filter-undefined-vars
	$(foreach var,$1,$(if $($(var)), $(var)))
endef

_CONF_VARS_BUILTIN = $(call filter-undefined-vars,$(CONF_VARS_BUILTIN))
_CONF_VARS = $(_CONF_VARS_BUILTIN) $(call filter-undefined-vars,$(CONF_VARS))

export $(_CONF_VARS)
export FAB_CHROOT_ENV = $(shell echo $(_CONF_VARS) | sed 's/ \+/:/g')
export FAB_INSTALL_ENV = $(FAB_CHROOT_ENV)

# FAB_PATH dependent infrastructural components
FAB_SHARE_PATH ?= /usr/share/fab
BOOTSTRAP ?= $(FAB_PATH)/bootstraps/$(CODENAME)
CDROOTS_PATH ?= $(FAB_PATH)/cdroots
CDROOT ?= generic
MKSQUASHFS ?= /usr/bin/mksquashfs
MKSQUASHFS_OPTS ?= -no-sparse

# if the CDROOT is a relative path, prefix CDROOTS_PATH
# we set _CDROOT with eval to improve the readability of $(value _CDROOT) 
# in help target
ifeq ($(shell echo $(CDROOT) | grep ^/), )
$(eval _CDROOT = $$(CDROOTS_PATH)/$(CDROOT))
else
$(eval _CDROOT = $(CDROOT))
endif

COMMON_OVERLAYS_PATH ?= $(FAB_PATH)/common/overlays
COMMON_CONF_PATH ?= $(FAB_PATH)/common/conf
COMMON_REMOVELISTS_PATH ?= $(FAB_PATH)/common/removelists

define prefix-relative-paths
	$(foreach val,$1,$(shell echo $(val) | sed '/^[^\/]/ s|^|$2/|' ))
endef

_COMMON_OVERLAYS = $(call prefix-relative-paths,$(COMMON_OVERLAYS),$(COMMON_OVERLAYS_PATH))
_COMMON_CONF = $(call prefix-relative-paths,$(COMMON_CONF),$(COMMON_CONF_PATH))
_COMMON_REMOVELISTS = $(call prefix-relative-paths,$(COMMON_REMOVELISTS),$(COMMON_REMOVELISTS_PATH))

FAB_PLAN_INCLUDE_PATH ?= $(FAB_PATH)/common/plans
export FAB_PLAN_INCLUDE_PATH

# default locations of product build inputs
PLAN ?= plan/main
ROOT_OVERLAY ?= overlay
CDROOT_OVERLAY ?= cdroot.overlay
REMOVELIST ?= removelist
# undefine REMOVELIST if the file doesn't exist
ifeq ($(wildcard $(REMOVELIST)),)
REMOVELIST =
endif

CONF_SCRIPTS ?= conf.d

INITRAMFS_PACKAGES ?= busybox-initramfs casper

# build output path
O ?= build

ISOLABEL ?= $(shell basename $(shell pwd))

STAMPS_DIR = $O/stamps

define remove-deck
	@if deck --isdeck $1; then \
		if [ "$$(basename $1)" = "root.tmp" ] && deck --isdirty $1; then \
			echo "error: root.tmp is dirty with manual changes. To continue: deck -D $(strip $1)"; \
			exit 1; \
		fi; \
		fuser -k $1; \
		echo deck -D $1; \
		deck -D $1; \
	fi
endef

ifdef CHROOT_ONLY
all: root.tmp
else
all: $O/product.iso
endif

define mount-deck
	@(deck $1 > /dev/null 2>&1) && echo deck $1 || true
endef

redeck:
	$(call mount-deck, $$(dirname $(PLAN)))
	$(call mount-deck, $(ROOT_OVERLAY))
	$(call mount-deck, $(CDROOT_OVERLAY))
	$(call mount-deck, $(CONF_SCRIPTS))
	$(call mount-deck, $O/bootstrap)
	$(call mount-deck, $O/root.build)
	$(call mount-deck, $O/root.patched)
	$(call mount-deck, $O/root.tmp)

debug:
	$(foreach v, $V, $(warning $v = $($v)))
	@true

define help/body
	@echo '=== Configurable variables'
	@echo 'Resolution order:'
	@echo '1) command line (highest precedence)'
	@echo '2) product Makefile'
	@echo '3) environment variable'
	@echo '4) built-in default (lowest precedence)'
	@echo
	@echo '# Mandatory variables        [VALUE]'
	@echo '  FAB_PATH                   $(value FAB_PATH)'
	@echo '  RELEASE                    $(value RELEASE)'
	@echo
	@echo '# Build context variables    [VALUE]'
	@echo '  CONF_VARS                  $(value CONF_VARS)'
	@echo
	@echo '  FAB_ARCH                   $(value FAB_ARCH)'
	@echo '  FAB_POOL                   $(value FAB_POOL)'
	@echo '  FAB_POOL_PATH              $(value FAB_POOL_PATH)'
	@echo '  FAB_PLAN_INCLUDE_PATH      $(value FAB_PLAN_INCLUDE_PATH)/'
	@echo '  CDROOTS_PATH               $(value CDROOTS_PATH)/'
	@echo '  COMMON_CONF_PATH           $(value COMMON_CONF_PATH)/'
	@echo '  COMMON_OVERLAYS_PATH       $(value COMMON_OVERLAYS_PATH)/'
	@echo '  COMMON_REMOVELISTS_PATH    $(value COMMON_REMOVELISTS_PATH)/'
	@echo
	
	@echo '# Local components           [VALUE]'
	@echo '  PLAN                       $(value PLAN)'
	@echo '  REMOVELIST                 $(value REMOVELIST)'
	@echo '  ROOT_OVERLAY               $(value ROOT_OVERLAY)/'
	@echo '  CONF_SCRIPTS               $(value CONF_SCRIPTS)/'
	@echo '  CDROOT_OVERLAY             $(value CDROOT_OVERLAY)/'
	@echo

	@echo '# Global components          [VALUE]'
	@echo '  POOL                       $(value POOL)/'
	@echo '  BOOTSTRAP                  $(value BOOTSTRAP)/'
	@echo '  CDROOT                     $(value CDROOT)'
	@echo '  MKSQUASHFS                 $(value MKSQUASHFS)'
	@echo '  MKSQUASHFS_OPTS            $(value MKSQUASHFS_OPTS)'
	@echo '  COMMON_CONF                $(value COMMON_CONF)'
	@echo '  COMMON_OVERLAYS            $(value COMMON_OVERLAYS)'
	@echo '  COMMON_REMOVELISTS         $(value COMMON_REMOVELISTS)'
	@echo

	@echo '# Product output variables   [VALUE]'
	@echo '  O                          $(value O)/'
	@echo '  ISOLABEL                   $(value ISOLABEL)'
	@echo
	@echo '# Built-in configuration options:'
	@echo '  DEBUG                      Turn on product debugging'
	@echo '  KERNEL                     Override default kernel package'
	@echo '  EXTRA_PLAN                 Extra packages to include in the plan'
	@echo '  CHROOT_ONLY                Build a chroot-only product'

	@echo 
	@echo '=== Usage'
	@echo '# remake target and the targets that depend on it'
	@echo '$$ rm $(value STAMPS_DIR)/<target>; make <target>'
	@echo
	@echo '# build a target (default: product.iso)'
	@echo '$$ make [target] [O=path/to/build/dir]'
	@echo '  redeck        # deck unmounted input/output decks (e.g., after reboot)'
	@echo
	@echo '  clean         # clean all build targets'
	@echo '  bootstrap     # minimal chrootable filesystem used to bootstrap the root'
	@echo '  root.spec     # the spec from which root.build is built (I.e., resolved plan)'
	@echo '  root.build    # created by applying the root.spec to the bootstrap'
	@echo '  root.patched  # deck root.build and apply the root overlay and removelist'
	@echo '  root.tmp      # temporary changes here are squashed into a separate layer'
endef

ifndef CHROOT_ONLY
help/body += ;\
	echo '  cdroot        \# created by squashing root.patched into cdroot template + overlay'; \
	echo '  product.iso   \# product ISO created from the cdroot'; \
	echo; \
	echo '  updated-initramfs \# rebuild product with updated initramfs' 
endif

help:
	$(help/pre)
	$(help/body)
	$(help/post)

define clean/body
	$(call remove-deck, $O/root.tmp)
	$(call remove-deck, $O/root.patched)
	$(call remove-deck, $O/root.build)
	$(call remove-deck, $O/bootstrap)
	-rm -rf $O/root.spec $O/cdroot $O/product.iso $O/log $(STAMPS_DIR)
endef

clean:
	$(clean/pre)
	$(clean/body)
	$(clean/post)

### STAMPED_TARGETS

# target: bootstrap
bootstrap/deps ?= $(BOOTSTRAP)
define bootstrap/body
	$(call remove-deck, $O/bootstrap)
	$(call remove-deck, $O/root.build)
	deck $(BOOTSTRAP) $O/bootstrap
endef

# target: root.spec
root.spec/deps ?= $(STAMPS_DIR)/bootstrap $(wildcard plan/*)
define root.spec/body
	fab-plan-resolve $(PLAN) $(EXTRA_PLAN) --bootstrap=$(BOOTSTRAP) --output=$O/root.spec $(foreach var,$(_CONF_VARS_BUILTIN),-D '$(var)=$($(var))')
endef

# target: root.build
root.build/deps ?= $(STAMPS_DIR)/bootstrap $(STAMPS_DIR)/root.spec
define root.build/init
	if ! deck --isdeck $O/root.build; then deck $O/bootstrap $O/root.build; fi
endef

define root.build/body
	@if [ -n "$(root.build/ignore-errors)" ]; then \
		opt_ignore_errors="--ignore-errors=$$(echo "$(root.build/ignore-errors)" | sed 's/ \+/:/g')"; \
	fi; \
	echo fab-install $$opt_ignore_errors $$FAB_INSTALL_OPTS $O/root.build $O/root.spec; \
	fab-install $$opt_ignore_errors $$FAB_INSTALL_OPTS $O/root.build $O/root.spec;
endef

define root.build/cleanup
	fuser -k $O/root.build || true
endef

# target: root.patched
define run-conf-scripts
	if [ -n "$(wildcard $1/*)" ]; then \
		echo "\$$(call $0,$1)"; \
	fi; \
	for script in $1/*; do \
		[ -f "$$script" ] && [ -x "$$script" ] || continue; \
		args_path=$(strip $1)/args/$$(echo $$(basename $$script) | sed 's/^[^a-zA-Z]*//'); \
		args="$$([ -f $$args_path ] && (cat $$args_path | sed 's/#.*//'))"; \
		[ -n "$$args" ] && args="-- $$args"; \
		\
		echo fab-chroot $O/root.patched --script $$script $$args; \
		fab-chroot $O/root.patched --script $$script $$args || exit; \
	done
endef

root.patched/deps ?= $(STAMPS_DIR)/root.build $(REMOVELIST) $(wildcard $(CONF_SCRIPTS)/*)
define root.patched/init
	$(call remove-deck, $O/root.patched)
	deck $O/root.build $O/root.patched
endef

define root.patched/body
	# apply the common overlays
	$(foreach overlay,$(_COMMON_OVERLAYS),
	  @if echo $(overlay) | grep -q '\.d$$'; then \
	  	for d in $(overlay)/*; do \
		  echo fab-apply-overlay $$d $O/root.patched; \
		  fab-apply-overlay $$d $O/root.patched; \
		done; \
	  else \
		  echo fab-apply-overlay $(overlay) $O/root.patched; \
		  fab-apply-overlay $(overlay) $O/root.patched; \
	  fi
	  )
	
	# run the common configuration scripts
	$(foreach conf,$(_COMMON_CONF),
	  @if [ -d $(conf) ]; then \
			$(call run-conf-scripts, $(conf)); \
	  else \
	  		echo fab-chroot $O/root.patched --script $(conf); \
	  		fab-chroot $O/root.patched --script $(conf); \
	  fi
	  )
	  
	# apply the common removelists
	$(foreach removelist,$(_COMMON_REMOVELISTS),
	  fab-apply-removelist $(removelist) $O/root.patched; \
	  )

	# apply the product-local root overlay
	if [ -d $(ROOT_OVERLAY) ]; then \
		fab-apply-overlay $(ROOT_OVERLAY) $O/root.patched; \
	fi

	# run the product-local configuration scripts
	@$(call run-conf-scripts, $(CONF_SCRIPTS))

	# apply the product-local removelist
	$(if $(REMOVELIST),fab-apply-removelist $(REMOVELIST) $O/root.patched)

	# update initramfs (handle reconfigured initramfs scripts)
	fab-chroot $O/root.patched "update-initramfs -u"
	fab-chroot $O/root.patched "rm -rf /boot/*.bak"
endef

define root.patched/cleanup
	# cleanup logs, caches and left over files
	fab-chroot $O/root.patched "rm -f /var/log/dpkg.log"
	fab-chroot $O/root.patched "rm -f /var/log/apt/*"
	fab-chroot $O/root.patched "rm -f /var/cache/apt/*.bin"
	fab-chroot $O/root.patched "rm -f /var/cache/apt/archives/*.deb"
	fab-chroot $O/root.patched "rm -rf /var/lib/apt/lists/*"

	# kill stray processes
	fuser -k $O/root.patched || true
endef

# target root.tmp
root.tmp/deps ?= $(STAMPS_DIR)/root.patched
define root.tmp/body
	$(call remove-deck, $O/root.tmp)
	deck $O/root.patched $O/root.tmp
endef

ifndef CHROOT_ONLY

# target: cdroot
cdroot/deps ?= $(STAMPS_DIR)/root.patched $(_CDROOT)
define cdroot/body
	if [ -e $O/cdroot ]; then rm -rf $O/cdroot; fi
	cp -a $(_CDROOT) $O/cdroot
	mkdir $O/cdroot/casper
	if [ -d $(CDROOT_OVERLAY) ]; then fab-apply-overlay $(CDROOT_OVERLAY) $O/cdroot; fi

	$(MKSQUASHFS) $O/root.patched $O/cdroot/casper/10root.squashfs $(MKSQUASHFS_OPTS)
endef

define run-genisoimage
	genisoimage -o $O/product.iso -r -J -l \
		-V ${ISOLABEL} \
		-b isolinux/isolinux.bin \
		-c isolinux/boot.cat \
		-no-emul-boot \
		-boot-load-size 4 \
		-boot-info-table $O/cdroot/
endef

define run-isohybrid
	isohybrid $O/product.iso
endef

# target: product.iso
define product.iso/body
	$(run-genisoimage)
	$(run-isohybrid)
endef

cdroot-dynamic: $(STAMPS_DIR)/root.tmp
	$(cdroot-dynamic/pre)
	$(cdroot-dynamic/body)
	$(cdroot-dynamic/post)

define cdroot-dynamic/body
	cp $O/root.tmp/usr/lib/syslinux/isolinux.bin $O/cdroot/isolinux
	cp $O/root.tmp/boot/$(shell basename $(shell readlink $O/root.tmp/vmlinuz)) $O/cdroot/casper/vmlinuz
	cp $O/root.tmp/boot/$(shell basename $(shell readlink $O/root.tmp/initrd.img)) $O/cdroot/casper/initrd.gz

	rm -f $O/cdroot/casper/20tmp.squashfs
	@if deck --isdirty $O/root.tmp; then \
		get_last_level="deck --get-level=last $O/root.tmp"; \
		output=$O/cdroot/casper/20tmp.squashfs; \
		echo "mksquashfs \$$($$get_last_level) $$output"; \
		\
		last_level=$$($$get_last_level); \
		mksquashfs $$last_level $$output; \
	fi;
endef

product.iso/deps ?= $(STAMPS_DIR)/cdroot cdroot-dynamic
$O/product.iso: $(product.iso/deps) $(product.iso/deps/extra)
	$(product.iso/pre)
	$(product.iso/body)
	$(product.iso/post)

product.iso: $O/product.iso

# target: updated-initramfs
define updated-initramfs/body
	rm -rf $O/product.iso
	$(root.patched/body)
	fab-install $$FAB_INSTALL_OPTS $O/root.patched $(INITRAMFS_PACKAGES)
	cp $O/root.patched/boot/$(shell basename $(shell readlink $O/root.patched/initrd.img)) $O/cdroot/casper/initrd.gz
	$(run-genisoimage)
endef


updated-initramfs/deps ?= $O/product.iso
updated-initramfs: $(update-initramfs/deps) $(updated-initramfs/deps/extra)
	$(updated-initramfs/pre)
	$(updated-initramfs/body)
	$(updated-initramfs/post)

endif

# construct target rules
define _stamped_target
$1: $(STAMPS_DIR)/$1

$(STAMPS_DIR)/$1: $$($1/deps) $$($1/deps/extra)
	@mkdir -p $(STAMPS_DIR)
	$$($1/init)
	$$($1/pre)
	$$($1/body)
	$$($1/post)
	$$($1/cleanup)
	touch $$@
endef

STAMPED_TARGETS := bootstrap root.spec root.build root.patched root.tmp cdroot
$(foreach target,$(STAMPED_TARGETS),$(eval $(call _stamped_target,$(target))))

.PHONY: all debug redeck help clean cdroot-dynamic updated-initramfs $(STAMPED_TARGETS) 
