#!/bin/bash

virtualenv --system-site-packages venv
source venv/bin/activate
python setup.py develop
