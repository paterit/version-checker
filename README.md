<!-- Updater documentation master file, created by
sphinx-quickstart on Thu Mar 14 21:29:00 2019.
You can adapt this file completely to your liking, but it should at least
contain the root `toctree` directive. -->
# Version updater for components in your codebase

## Problem to solve

In project where there are many components to track new versions (docker
images and pypi packages) this tool automates finding new versions,
running tests and commit changes to git.

## TL;DR

Create YAML file with definition of your components (see example in
[tests/test_files/components.yaml](https://github.com/paterit/version-checker/blob/master/tests/test_files/components.yaml) ). Place `components.yaml` in the
root of your project directory and run:

`python check_version.py --file=/path/to/your/components.yaml --dry-run check --verbose`

It will, for each defined component:

1. Check if there are new versions of your components available

1. Replace in all files version numbers to the newest one

1. Run tests

1. Add and commit changes to git

## Installation

Install via pypi packages repository:

`pip install updater`

## Usage

### updater

```
updater [OPTIONS] COMMAND [ARGS]...
```

### Options


#### --file <file>
YAML file with components configuration. If not present other options for ‘check’ command are required.


#### --destination-file <destination_file>
If this option is given components configuration with new versions will be wrtten here.


#### --dry-run
If set no changes to any files are written.


#### --print
Config is printed to stdout at the end.

#### check

Check if new versions of defined components are available.

```
updater check [OPTIONS]
```

### Options


#### --type <component_type>
Component type: docker-image or pypi package.


#### --component <component>
Component name to version veryfication.


#### --repo_name <repo_name>
Repository name if component is docker image.


#### --version_tag <version_tag>
Version tag eg. v2.3.0 against which new version check will be run.


#### --verbose
Print detailed info for each component about new version avaialble.

#### update

Update files with version numbers, run test and commit changes.

```
updater update [OPTIONS]
```

### Options


#### --test-command <test_command>
Command that should be run after updating each component.


#### --test-dir <test_dir>
If test-command param is given, this will be the context dir to run it.


#### --git-commit
When set after each components update, git commit is performed in active branch.


#### --project-dir <project_dir>
If given, then it will be treated as a root dir for paths in config file.

<!-- Indices and tables
==================
* :ref:`genindex`
* :ref:`modindex`
* :ref:`search` -->
