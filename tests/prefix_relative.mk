VAR ?= relative
PREFIX = /home/user

ifeq ($(shell echo $(VAR) | grep ^/), )
$(eval _VAR = $$(PREFIX)/$(VAR))
else
$(eval _VAR = $(VAR))
endif

test:
	@echo 'value _VAR=$(value _VAR)'
	@echo '_VAR=$(_VAR)'
	


