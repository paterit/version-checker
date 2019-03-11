# Version updater for components in your codebase

## Problem to solve

In project where there are many components to track new versions (docker images and pypi packages) this tool automates finding new versions, running tests and commit changes to git.

## TL;DR

Create YAML file with definition of your components (see example in `tests/test_files/components.yaml`). Place components.yaml in the root of your project directory and run:

`python check_version.py --file=/path/to/your/components.yaml --dry-run check`

It will, for each defined component:
1. Check if there are new versions of your components available
1. Replace in all files version numbers to the newest one
1. Run tests
1. Add and commit changes to git
