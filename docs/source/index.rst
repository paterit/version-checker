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


Config file format
------------------

Example of one component definition:

.. code-block:: yaml

   # name of the component
   python:
      # docker-image or pypi
      component-type: docker-image
      # this version tak needs to aligned with versions in files
      # if you put "latest" then check and update will be skipped for this component
      current-version: 3.6.6-alpine3.8
      # for docker-image component-type only
      docker-repo: library
      # filter used to get all possible versions
      filter: /^\d+\.\d+\.\d+-alpine\d+\.\d+$/
      # files in which version number should be replaced
      files: [locust/Dockerfile, locust/some_script.sh]
      # this is the find (current version) and replace (new version) pattern.
      # {version} and {component} can be used
      version-pattern: "PYTHON_VERSION {version}"
      # if there are different patterns in particular files, you can specify them here
      # file level pattern overrides component level pattern
      files-version-pattern:
         - file: locust/Dockerfile
            pattern: PYTHON_VERSION={version}
         - file: locust/some_script.sh
            pattern: version {version}
   Django:
      component-type: pypi
      current-version: 2.2.24
      filter: /^\d+\.\d+(\.\d+)?$/
      files: [app/requirements.txt]
   logspout:
      component-type: docker-image
      current-version: v3.1
      docker-repo: gliderlabs
      filter: /^v\d+\.\d+\.\d+$/
      # if there is prefix before numeric part of version, you can specify it here
      prefix: v
      files: [logspout/Dockerfile-logspout]
      # put here versions which should be skipped
      exclude-versions: [v3.2.6]

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
