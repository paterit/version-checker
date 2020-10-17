check:
	@pipenv run \
		python check_version.py \
		--file=tests/test_files/components.yaml \
		--dry-run \
		check

update:
	@pipenv run \
		python check_version.py \
		--file=tests/test_files/components.yaml \
		--dry-run \
		update \
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
	pipenv run python -m pytest --disable-warnings -vv -x -m "not slow"
pytest-all:
	pipenv run python -m pytest --disable-warnings -vv -x
pytest-wip:
	pipenv run python -m pytest --disable-warnings -vv -m wip
pytest-help:
	pipenv run python -m pytest --help
black: 
	pipenv run black .
test:
	make pytest
	make sbe

pipenv-clean:
	rm -rf .venv Pipfile.lock
pipenv-install:
	pipenv install -d

package-dist: clean-package-dist
	pipenv run python setup.py sdist bdist_wheel
	pipenv run python -m twine upload dist/*
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

pyenv-install:
	pyenv install 3.8.6
	pyenv local 3.8.6
	python -m pip install tox
	pyenv install 3.7.9
	pyenv local 3.7.9
	python -m pip install tox
	pyenv install 3.6.12
	pyenv local 3.6.12
	python -m pip install tox
	pyenv local 3.8.6 3.7.9 3.6.12

cov-pytest:
	pipenv run python -m coverage run --source=updater -m pytest --disable-warnings -vv -x
	pipenv run python -m coverage report -m

cov-sbe:
	pipenv run python -m coverage run --source=updater -m behave --tags=-skip --tags=-wip --stop --no-skipped tests/features
	pipenv run python -m coverage report -m

cov:
	pipenv run python -m coverage run --source=updater -a -m pytest --disable-warnings -vv -x
	pipenv run python -m coverage run --source=updater -a -m behave --tags=-skip --tags=-wip --stop --no-skipped tests/features
	pipenv run python -m coverage report -m
