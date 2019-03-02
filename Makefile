build:
	docker build -t paterit/version-checker .
	sed -i "s|STARTER_PROJECT_DIR|`pwd`|g" ./version-checker.sublime-project
	docker run -it -v `pwd`:`pwd` -w `pwd` --rm --name version-checker paterit/version-checker pipenv install -d
	make subl-anaconda-docker-run
shell:
	@docker exec -it -w `pwd` version-checker bash
run:
	@docker exec -it -w `pwd` version-checker pipenv run \
		python check_version.py \
		--file=tests/test_files/components.yaml \
		--destination-file=tmp_comp.yaml \
		check
sbe:
	@docker exec -it -w `pwd` version-checker pipenv run behave --tags=-skip --stop --no-skipped tests/features
sbe-wip:
	@docker exec -it -w `pwd` version-checker pipenv run behave --tags=wip --stop --no-skipped --no-summary tests/features
pytest:
	@docker exec -it -w `pwd` version-checker pipenv run python -m pytest --disable-warnings -vv
pytest-help:
	@docker exec -it -w `pwd` version-checker pipenv run python -m pytest --help
black: 
	@docker exec -it -w `pwd` version-checker pipenv run black .
test:
	make pytest
	make sbe


subl-anaconda-docker-run:
	# make sure ~/.config/sublime-text-3/Packages/Anaconda/anaconda_server/docker/start has +x flag set (executable script)
	docker run -d --rm -p 19360:19360 --name version-checker \
			-v ~/.config/sublime-text-3/Packages/Anaconda:/opt/anaconda \
			-v `pwd`:`pwd` \
			-w `pwd` \
			-e "PYTHONPATH=`pwd`" \
			paterit/version-checker \
			/opt/anaconda/anaconda_server/docker/start `pwd`/.venv/bin/python 19360 starter

subl-anaconda-docker-stop:
	docker stop version-checker

pipenv-clean:
	-docker stop version-checker
	sudo rm -rf .venv Pipfile.lock
pipenv-chown:
	sudo chown $(USER):$(USER) -R .venv/ Pipfile Pipfile.lock
pipenv-install:
	docker exec -it -w `pwd` version-checker pipenv install -d


