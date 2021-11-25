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

``python check_version.py --file=/path/to/your/components.yaml --dry-run check --verbose``

It will, for each defined component: 

#) Check if there are new versions of your components available 
#) Replace in all files version numbers to the newest one 
#) Run tests
#) Add and commit changes to git

Installation
------------

Install via pypi packages repository:

``pip install updater``

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
