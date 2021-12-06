<!-- Updater documentation master file, created by
sphinx-quickstart on Thu Mar 14 21:29:00 2019.
You can adapt this file completely to your liking, but it should at least
contain the root `toctree` directive. -->
# Version updater for components in your codebase

## Problem to solve

In the project where there are many components to track new versions (docker
images and pypi packages) this tool automates finding new versions,
running tests and commit changes to git.

## TL;DR

Create YAML file with definition of your components (see example in
[tests/test_files/components.yaml](https://github.com/paterit/version-checker/blob/master/tests/test_files/components.yaml) ). Place `components.yaml` in the
root of your project directory and run:

```python
>>> python -m updater check
10 components to check
1 components to update
```

```python
>>> python -m updater check --verbose
10 components to check
1 components to update
pymongo - current: 3.12.1 next: 3.12.2
```

This will check versions for all components defined in `components2.yaml`:

```python
>>> python -m updater --file=/path/to/your/components2.yaml check
10 components to check
1 components to update
```

Here is an example of update script which will do checking and print out updated config file without making any changes in your files:

```python
>>> python -m updater --dry-run --print update
```

Here is full example of using update command:

```python
>>> python -m updater update --git-commit --test-command="make test"
```

It will, for each defined component in `components.yaml` from the local directory:


1. Check if there are new versions of your components available


2. Replace in all files version numbers to the newest one


3. Run tests


4. Add and commit changes to git

## Installation

Install via pypi packages repository:

```python
>>> python -m pip install updater
```

## YAML Config file format

Example of components definition:

```
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
```

## Import python packages to components.yaml

If you want to “copy” python packages to components.yaml from requirements.txt, pipfile (pipenv)
or Poetry (project.toml) you need use `import-req` command with `--source` set to one of
`requirements`, `pipfile` or `poetry`. In each cases the `--requirements-file` param needs to point at
requirements.txt like file but will set proper `version-pattern` and `files`.

## Usage

### updater

```
updater [OPTIONS] COMMAND [ARGS]...
```

### Options


#### --version
Show the version and exit.


#### --file <file>
YAML file with components configuration. If not present other options for ‘check’ command are required.


#### --destination-file <destination_file>
If this option is given components configuration with new versions will be written here.


#### --dry-run
If set no changes to any files are written.


#### --print
Config is printed to stdout at the end.

#### check

Check if new versions of ddefined components are available.

```
updater check [OPTIONS]
```

### Options


#### --type <component_type>
Component type: docker-image or pypi package.


* **Options**

    docker-image|pypi



#### --component <component>
A component name for which the version should be verified.


#### --repo_name <repo_name>
A repository name if component is a docker image.


#### --version_tag <version_tag>
Version tag eg. v2.3.0 against which new version check will be run.


#### --verbose
Print detailed info for each component about new version avaialble.


#### --clear-cache
Clear all the cached responses about versions in rpositories.


#### --ignore-default-file
Ignore components.yaml file in local directory if exists.

#### import-req

Imports python packages from requirements.txt file.

```
updater import-req [OPTIONS]
```

### Options


#### --source <source>
Source of the requirement.txt file.  [required]


* **Options**

    requirements|pipfile|poetry



#### --requirements-file <requirements_file>
Requirements.txt file from which packages and versions will be added to components.yaml file.  [required]

#### update

Update files, run test and commit changes.

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


#### -v(, --verbose
Print at the end detailed info for each component about update process.


#### -vv(, --very-verbose
Print at the end detailed info for each component about update process.

<!-- Indices and tables
==================
* :ref:`genindex`
* :ref:`modindex`
* :ref:`search` -->
