build:
	docker build -t paterit/version-checker .
	sed -i "s|STARTER_PROJECT_DIR|`pwd`|g" ./version-checker.sublime-project
	docker run -it -v `pwd`:`pwd` -w `pwd` --rm --name version-checker paterit/version-checker pipenv install -d
	make subl-anaconda-docker
shell:
	@docker exec -it -w `pwd` version-checker bash
run:
	@docker exec -it -w `pwd` version-checker pipenv run python check-version.py
sbe:
	@docker exec -it -w `pwd` version-checker pipenv run behave --tags=-skip --no-skipped tests/features
pytest:
	@docker exec -it -w `pwd` version-checker pipenv run pytest
black: 
	@docker exec -it -w `pwd` version-checker pipenv run black .
test:
	make pytest
	make sbe


subl-anaconda-docker:
	# make sure ~/.config/sublime-text-3/Packages/Anaconda/anaconda_server/docker/start has +x flag set (executable script)
	docker run -d --rm -p 19360:19360 --name version-checker \
			-v ~/.config/sublime-text-3/Packages/Anaconda:/opt/anaconda \
			-v `pwd`:`pwd` paterit/version-checker \
			/opt/anaconda/anaconda_server/docker/start `pwd`/.venv/bin/python 19360 starter


pipenv-clean:
	-docker stop version-checker
	sudo rm -rf .venv Pipfile.lock
pipenv-chown:
	sudo chown $(USER):$(USER) -R .venv/ Pipfile Pipfile.lock
pipenv-install:
	docker exec -it -w `pwd` version-checker pipenv install -d

