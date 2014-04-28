#!/bin/sh
python setup.py register -r ltj sdist upload -r ltj

# install command:
#pip install -U -b /tmp --extra-index-url http://adweb1:8000/pypi/ pygaga

