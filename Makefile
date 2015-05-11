VENV = venv
PYTHON_CMD = $(VENV)/bin/python
PYTHON_FILES := $(shell find forge/ -name '*.py')

.PHONY: help
help:
	@echo "Usage: make <target>"
	@echo
	@echo "Possible targets:"
	@echo
	@echo "- install            Install the app"
	@echo "- lint               Linter for python code"
	@echo "- all                All of the above"
	@echo "- autolint           Auto lint code styling"
	@echo "- clean              Clean all generated files and folders"
	@echo
	@echo "Variables:"
	@echo
	@echo "- PYTHON_CMD (current value: $(PYTHON_CMD))"

	@echo

.PHONY: all
all: install lint

.PHONY: install
install:
	virtualenv $(VENV) --system-site-packages
	$(PYTHON_CMD) setup.py develop

.PHONY: lint
lint:
	venv/bin/flake8 --ignore=E501 forge/

.PHONY: autolint
autolint:
	@echo $(PYTHON_FILES)
	venv/bin/autopep8 -v -i -a --ignore=E501 $(PYTHON_FILES)

.PHONY: clean
clean:
	rm -rf venv
	rm -rf *.egg-info
