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
	@echo "- test               Launch the tests"
	@echo "- all                All of the above"
	@echo "- autolint           Auto lint code styling"
	@echo "- updatesubmodule    Update 3d testapp"
	@echo "- serve              Serve examples in localhost (usage make serve PORT=9005)"
	@echo "- createdb           Create the database"
	@echo "- importshp          Imports shapefiles"
	@echo "- dropdb             Drop the database"
	@echo "- tmspyramid         Create the TMS pyramid based on the config file tms.cfg"
	@echo "- tmsstats           Provide statistics about the TMS pyramid"
	@echo "- clean              Clean all generated files and folders"
	@echo
	@echo "Variables:"
	@echo
	@echo "- PYTHON_CMD (current value: $(PYTHON_CMD))"

	@echo

.PHONY: all
all: install database.cfg apache/testapp.conf test lint

.PHONY: install
install:
	virtualenv $(VENV) --system-site-packages
	$(PYTHON_CMD) setup.py develop
	$(VENV)/bin/pip install local_eggs/GeoAlchemy2-0.2.4-ga3.tar.gz

apache/testapp.conf: apache/testapp.conf.mako
	$(VENV)/bin/mako-render --var "user=$(USERNAME)" --var "directory=$(CURDIR)" $< > $@

database.cfg: database.cfg.mako
	$(VENV)/bin/mako-render --var "pgpass=$(PGPASS)" --var "dbtarget=$(DBTARGET)" $< > $@

.PHONY: lint
lint:
	venv/bin/flake8 --ignore=E501 forge/

.PHONY: test
test:
	$(VENV)/bin/nosetests forge/tests/

.PHONY: autolint
autolint:
	@echo $(PYTHON_FILES)
	$(VENV)/bin/autopep8 -v -i -a --ignore=E501 $(PYTHON_FILES)

.PHONY: updatesubmodule
updatesubmodule:
	git submodule update
	git submodule foreach git pull origin master

.PHONY: serve
serve:
	$(PYTHON_CMD) forge/scripts/http_server.py $(PORT)

.PHONY: createdb
createdb:
	$(PYTHON_CMD) forge/scripts/db_management.py create

.PHONY: importshp
importshp:
	$(PYTHON_CMD) forge/scripts/db_management.py importshp

.PHONY: dropdb
dropdb:
	$(PYTHON_CMD) forge/scripts/db_management.py destroy

.PHONY: tmspyramid
tmspyramid:
	$(PYTHON_CMD) forge/scripts/tms_writer.py create

.PHONY: tmsstats
tmsstats:
	$(PYTHON_CMD) forge/scripts/tms_writer.py stats

.PHONY: clean
clean:
	rm -rf venv
	rm -rf *.egg-info
	rm -rf 3d-testapp
	rm -f apache/testapp.conf
	rm -f .tmp/*.*
