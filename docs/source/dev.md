# How to do development of updater

## Test with tox

1. Install `pyenv`
1. Validate python versions in `Makefile` `pyenv-install` target
1. Run `make pyenv-install`
1. Run `make tox` to test against all versions defined in `tox.ini`

## Set up local python for development (how I do it)

1. Install `pyenv`
1. Validate python versions in `Makefile` `pyenv-install` target
1. Run `make pyenv-install`
1. Run `make venv-with-pipenv`
1. Check if your python is run from the proper dir with `which python`. Run `source .venv/bin/activate` if in doubts.
1. Run `make pipenv-install` to install dependencies then `make test-pipenv-install` to run tests
