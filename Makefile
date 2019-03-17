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

help:
	pipenv run python check_version.py --help

sbe:
	pipenv run behave --tags=-skip --tags=-wip --stop --no-skipped tests/features
sbe-wip:
	pipenv run behave --tags=wip --stop --no-skipped --no-summary tests/features
pytest:
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
	python setup.py sdist bdist_wheel
	python -m twine upload dist/*
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

