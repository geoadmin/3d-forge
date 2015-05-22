VENV = venv
PYTHON_CMD = $(VENV)/bin/python
PORT ?= 9025
PYTHON_FILES := $(shell find forge/ -name '*.py')
USERNAME := $(shell whoami)

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
	@echo "- serve              Serve examples in localhost (usage make serve PORT=9005)"
	@echo "- clean              Clean all generated files and folders"
	@echo
	@echo "Variables:"
	@echo
	@echo "- PYTHON_CMD (current value: $(PYTHON_CMD))"

	@echo

.PHONY: all
all: install apache/testapp.conf lint

.PHONY: install
install:
	virtualenv $(VENV) --system-site-packages
	$(PYTHON_CMD) setup.py develop

apache/testapp.conf: apache/testapp.conf.mako
	$(VENV)/bin/mako-render --var "user=$(USERNAME)" --var "directory=$(CURDIR)" $< > $@

.PHONY: lint
lint:
	venv/bin/flake8 --ignore=E501 forge/

.PHONY: autolint
autolint:
	@echo $(PYTHON_FILES)
	$(VENV)/bin/autopep8 -v -i -a --ignore=E501 $(PYTHON_FILES)

.PHONY: serve
serve:
	$(PYTHON_CMD) forge/scripts/http_server.py $(PORT)

.PHONY: clean
clean:
	rm -rf venv
	rm -rf *.egg-info
