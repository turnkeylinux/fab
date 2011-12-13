#!/usr/bin/make -f
# Copyright (c) 2011-2012 TurnKey Linux - all rights reserved

ifndef FAB_PATH
$(error FAB_PATH not defined - needed for default paths)
endif

ifndef RELEASE
$(warning RELEASE not defined - default paths for POOL and BOOTSTRAP may break)
endif

_CONF_VARS = RELEASE $(foreach var,$(CONF_VARS),$(if $($(var)), $(var)))
export $(_CONF_VARS)
export FAB_CHROOT_ENV = $(shell echo $(_CONF_VARS) | sed 's/ \+/:/g')

# FAB_PATH dependent infrastructural components
POOL ?= $(FAB_PATH)/pools/$(RELEASE)
BOOTSTRAP ?= $(FAB_PATH)/bootstraps/$(RELEASE)
CDROOTS_PATH ?= $(FAB_PATH)/cdroots
CDROOT ?= generic

# if the CDROOT is a relative path, prefix CDROOTS_PATH
# we set _CDROOT with eval to improve the readability of $(value _CDROOT) 
# in help target
ifeq ($(shell echo $(CDROOT) | grep ^/), )
$(eval _CDROOT = $$(CDROOTS_PATH)/$(CDROOT))
else
$(eval _CDROOT = $(CDROOT))
endif

RELEASE_OVERLAY ?= $(FAB_PATH)/common-overlays/$(RELEASE)
RELEASE_CONF_SCRIPTS ?= $(FAB_PATH)/common-conf.d/$(RELEASE)

FAB_PLAN_INCLUDE_PATH ?= $(FAB_PATH)/common-plans

export FAB_POOL_PATH = $(POOL)
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
		echo deck -D $1; \
		deck -D $1; \
	fi
endef

all: $O/product.iso

define mount-deck
	@(deck $1 > /dev/null 2>&1) && echo deck $1 || true
endef

redeck:
	$(call mount-deck, $$(dirname $(PLAN)))
	$(call mount-deck, $(RELEASE_OVERLAY))
	$(call mount-deck, $(RELEASE_CONF_SCRIPTS))
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
	@echo '# Mandatory configuration variables:'
	@echo '  FAB_PATH and RELEASE       used to calculate default paths for input variables'
	@echo
	@echo '# Build context variables    [VALUE]'
	@echo '  CONF_VARS                  $(value CONF_VARS)'
	@echo
	@echo '  POOL                       $(value POOL)/'
	@echo '  BOOTSTRAP                  $(value BOOTSTRAP)/'
	@echo '  CDROOTS_PATH               $(value CDROOTS_PATH)/'
	@echo '  CDROOT                     $(value _CDROOT)/'
	@echo '  FAB_PLAN_INCLUDE_PATH      $(value FAB_PLAN_INCLUDE_PATH)/'
	@echo
	@echo '# Release input variables    [VALUE]'
	@echo '  RELEASE_OVERLAY            $(value RELEASE_OVERLAY)/'
	@echo '  RELEASE_CONF_SCRIPTS       $(value RELEASE_CONF_SCRIPTS)/'
	@echo
	@echo '# Product input variables    [VALUE]'
	@echo '  PLAN                       $(value PLAN)'
	@echo '  ROOT_OVERLAY               $(value ROOT_OVERLAY)/'
	@echo '  CDROOT_OVERLAY             $(value CDROOT_OVERLAY)/'
	@echo '  REMOVELIST                 $(value REMOVELIST)'
	@echo '  CONF_SCRIPTS               $(value CONF_SCRIPTS)/'
	@echo

	@echo '# Product output variables   [VALUE]'
	@echo '  O                          $(value O)/'
	@echo '  ISOLABEL                   $(value ISOLABEL)'
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
	@echo '  cdroot        # created by squashing root.patched into cdroot template + overlay'
	@echo '  product.iso   # product ISO created from the cdroot'
	@echo
	@echo '  updated-initramfs # rebuild product with updated initramfs'
endef

help:
	$(help/pre)
	$(help/body)
	$(help/post)

define clean/body
	$(call remove-deck, $O/root.tmp)
	$(call remove-deck, $O/root.patched)
	$(call remove-deck, $O/root.build)
	$(call remove-deck, $O/bootstrap)
	-rm -rf $O/root.spec $O/cdroot $O/product.iso $(STAMPS_DIR)
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
	fab-plan-resolve $(PLAN) $O/bootstrap --output=$O/root.spec $(foreach var,$(_CONF_VARS),-D $(var)=$($(var)))
endef

# target: root.build
root.build/deps ?= $(STAMPS_DIR)/bootstrap $(STAMPS_DIR)/root.spec
define root.build/body
	if ! deck --isdeck $O/root.build; then deck $O/bootstrap $O/root.build; fi
	fab-install --no-deps $O/root.build $O/root.spec
endef

# target: root.patched
define run-conf-scripts
	@if [ -n "$(wildcard $1/*)" ]; then \
		echo "\$$(call $0,$1)"; \
	fi
	@for script in $1/*; do \
		[ -f "$$script" ] && [ -x "$$script" ] || continue; \
		args_path=$(strip $1)/args/$$(echo $$(basename $$script) | sed 's/^[^a-zA-Z]*//'); \
		args="$$([ -f $$args_path ] && (cat $$args_path | sed 's/#.*//'))"; \
		[ -n "$$args" ] && args="-- $$args"; \
		\
		echo fab-chroot $O/root.patched --script $$script $$args; \
		fab-chroot $O/root.patched --script $$script $$args; \
	done
endef

root.patched/deps ?= $(STAMPS_DIR)/root.build $(REMOVELIST) $(wildcard $(CONF_SCRIPTS)/*)
define root.patched/body
	$(call remove-deck, $O/root.patched)
	deck $O/root.build $O/root.patched
	if [ -d $(RELEASE_OVERLAY) ]; then \
		fab-apply-overlay $(RELEASE_OVERLAY) $O/root.patched; \
	fi
	$(call run-conf-scripts, $(RELEASE_CONF_SCRIPTS))
	if [ -d $(ROOT_OVERLAY) ]; then \
		fab-apply-overlay $(ROOT_OVERLAY) $O/root.patched; \
	fi
	fab-chroot $O/root.patched "rm -rf /boot/*.bak"
	$(call run-conf-scripts, $(CONF_SCRIPTS))
	$(if $(REMOVELIST),fab-apply-removelist $(REMOVELIST) $O/root.patched)
endef

# target root.tmp
root.tmp/deps ?= $(STAMPS_DIR)/root.patched
define root.tmp/body
	$(call remove-deck, $O/root.tmp)
	deck $O/root.patched $O/root.tmp
endef

# target: cdroot
cdroot/deps ?= $(STAMPS_DIR)/root.patched $(_CDROOT)
define cdroot/body
	if [ -e $O/cdroot ]; then rm -rf $O/cdroot; fi
	cp -a $(_CDROOT) $O/cdroot
	mkdir $O/cdroot/casper
	if [ -d $(CDROOT_OVERLAY) ]; then fab-apply-overlay $(CDROOT_OVERLAY) $O/cdroot; fi

	mksquashfs $O/root.patched $O/cdroot/casper/10root.squashfs
endef

# construct target rules
define _stamped_target
$1: $(STAMPS_DIR)/$1

$(STAMPS_DIR)/$1: $$($1/deps) $$($1/deps/extra)
	@mkdir -p $(STAMPS_DIR)
	$$($1/pre)
	$$($1/body)
	$$($1/post)
	touch $$@
endef

STAMPED_TARGETS := bootstrap root.spec root.build root.patched root.tmp cdroot
$(foreach target,$(STAMPED_TARGETS),$(eval $(call _stamped_target,$(target))))

define run-genisoimage
	genisoimage -o $O/product.iso -r -J -l \
		-V ${ISOLABEL} \
		-b isolinux/isolinux.bin \
		-c isolinux/boot.cat \
		-no-emul-boot \
		-boot-load-size 4 \
		-boot-info-table $O/cdroot/
endef

# target: product.iso
define product.iso/body
	$(run-genisoimage)
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
	fab-install --no-deps $O/root.patched $(INITRAMFS_PACKAGES)
	cp $O/root.patched/boot/$(shell basename $(shell readlink $O/root.patched/initrd.img)) $O/cdroot/casper/initrd.gz
	$(run-genisoimage)
endef


updated-initramfs/deps ?= $O/product.iso
updated-initramfs: $(update-initramfs/deps) $(updated-initramfs/deps/extra)
	$(updated-initramfs/pre)
	$(updated-initramfs/body)
	$(updated-initramfs/post)

.PHONY: all debug redeck help clean cdroot-dynamic updated-initramfs $(STAMPED_TARGETS) 
