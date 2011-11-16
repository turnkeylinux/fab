NAME ?= liraz
AGE ?= 27
VARS ?= NAME AGE HEIGHT

_VARS = $(foreach var,$(VARS),$(if $($(var)), $(var)))

export $(_VARS)

test:
	@echo $(_VARS)
	@echo $(foreach var,$(_VARS),-D $(var)=$($(var)))
	@echo $(shell echo $(_VARS) | sed 's/ \+/:/g')
	env | grep HEIGHT
