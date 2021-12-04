.. Updater documentation master file, created by
   sphinx-quickstart on Thu Mar 14 21:29:00 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.


Version updater for components in your codebase
===============================================


Problem to solve
----------------

In the project where there are many components to track new versions (docker
images and pypi packages) this tool automates finding new versions,
running tests and commit changes to git.

TL;DR
-----

Create YAML file with definition of your components (see example in
`tests/test_files/components.yaml`_ ). Place ``components.yaml`` in the
root of your project directory and run:

>>> python -m updater check
10 components to check
1 components to update

>>> python -m updater check --verbose
10 components to check
1 components to update
pymongo - current: 3.12.1 next: 3.12.2


This will check versions for all components defined in ``components2.yaml``:

>>> python -m updater --file=/path/to/your/components2.yaml check 
10 components to check
1 components to update

Here is an example of update script which will do checking and print out update config file without making any changes in your files:

>>> python -m updater --dry-run --print update

Here is full example of using update command:

>>> python -m updater update --git-commit --test-command="make test"

It will, for each defined component in ``components.yaml`` from local directory: 

#) Check if there are new versions of your components available 
#) Replace in all files version numbers to the newest one 
#) Run tests
#) Add and commit changes to git

Installation
------------

Install via pypi packages repository:

>>> python -m pip install updater

.. _tests/test_files/components.yaml: https://github.com/paterit/version-checker/blob/master/tests/test_files/components.yaml

Usage
-----

.. click:: check_version:cli
   :prog: updater
   :show-nested:



.. Indices and tables
 ==================
 * :ref:`genindex`
 * :ref:`modindex`
 * :ref:`search`
