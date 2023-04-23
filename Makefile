check:
	@pipenv run \
		python check_version.py \
		--file=tests/test_files/components.yaml \
		--dry-run \
		check \
		--verbose

update:
	@pipenv run \
		python check_version.py \
		--file=tests/test_files/components.yaml \
		--dry-run \
		update \
		--verbose

self-check:
	@pipenv run \
		python check_version.py \
		check \
		--verbose

self-update:
	@pipenv run \
		python check_version.py \
		update \
		--verbose \
		--test-command="make test-pipenv-install"

self-import-req:
	@pipenv run \
		python check_version.py \
		--file=components.yaml \
		import-req \
		--requirements-file=requirements.txt \
		--verbose


clear-cache:
	@pipenv run python check_version.py check --clear-cache

help:
	pipenv run python check_version.py --help

sbe:
	pipenv run behave --tags=-skip --tags=-wip --stop --no-skipped tests/features
sbe-wip:
	pipenv run behave --tags=wip --stop --no-skipped --no-summary --no-logcapture --no-capture-stderr --no-logcapture --logging-level=DEBUG tests/features
pytest:
	pipenv run python -m pytest --disable-warnings -vv -x --durations=5 -m "not slow" --exitfirst --showlocals --tb=long
pytest-all:
	pipenv run python -m pytest --disable-warnings -vv -x
pytest-wip:
	pipenv run python -m pytest --disable-warnings -vv -m wip
pytest-help:
	pipenv run python -m pytest --help
pytest-config:
	pipenv run python -m pytest --disable-warnings -vv -m "not slow" --exitfirst --showlocals --tb=long tests/pytest/test_config_yaml.py
pytest-component:
	pipenv run python -m pytest --disable-warnings -vv -m "not slow" --exitfirst tests/pytest/test_components.py
black: 
	pipenv run black .
test:
	make pytest
	make sbe
test-all:
	make pytest-all
	make sbe

venv-with-pipenv:
	pyenv local 3.11
	python -m venv .venv
	python -m pip install --upgrade pip
	python -m pip install pipenv

test-pipenv-install:
	pipenv install --skip-lock
	make pytest
	make sbe

pipenv-clean:
	rm -rf .venv Pipfile.lock
pipenv-install:
	pipenv install --skip-lock -d

package-dist: clean-package-dist
	pipenv run python setup.py sdist bdist_wheel
	pipenv run python -m twine upload --config-file ./.pypirc dist/*
	git tag -f -a `cat updater/VERSION` -m "New relase `cat updater/VERSION`"
	git push origin --tags
	make clean-package-dist

clean-package-dist:
	rm -rf build dist updater.egg-info

clean-docs:
	rm -rf docs/build

build-docs: clean-docs
	cd docs && \
		make html && \
		make markdown
	cd docs && \
		find . -name *.md | xargs sed -i 's/( </ </g' && \
		find . -name *.md | xargs sed -i 's/>)/>/g' && \
		find . -name *.md | xargs sed -i 's/()//g'
	cp docs/build/markdown/index.md ./README.md

blackd:
	docker run -d --rm -p 45484:45484 --name blackd paterit/blackd

tox:
	python -m tox

# to list all available versions: `pyenv install -l`
pyenv-install:
	pyenv install -s 3.8.16
	pyenv local 3.8.16
	python -m pip install --upgrade pip
	python -m pip install tox
	pyenv install -s 3.7.16
	pyenv local 3.7.16
	python -m pip install --upgrade pip
	python -m pip install tox
	# pyenv install 3.6.15
	# pyenv local 3.6.15
	# python -m pip install tox
	pyenv install -s 3.9.16
	pyenv local 3.9.16
	python -m pip install --upgrade pip
	python -m pip install tox
	pyenv install -s 3.10.11
	pyenv local 3.10.11
	python -m pip install --upgrade pip
	python -m pip install tox
	pyenv install -s 3.11.3
	pyenv local 3.11.3
	python -m pip install --upgrade pip
	python -m pip install tox
	pyenv local 3.8.16 3.7.16 3.9.16 3.10.11 3.11.3

cov:
	pipenv run python -m coverage run --source=updater -m pytest --disable-warnings -vv -x 
	pipenv run python -m coverage report -m

cov-all:
	pipenv run python -m coverage run --source=. --omit="*/.venv/*,*/tests/*,setup.py" -m pytest --disable-warnings -vv -x 
	pipenv run python -m coverage report -m

mypy:
	pipenv run python -m mypy --strict --show-error-codes check_version.py
