build:
	docker build -t paterit/starter-selenium .
	sed -i "s|STARTER_PROJECT_DIR|`pwd`|g" ./starter.sublime-project
	docker run -it -v `pwd`:`pwd` -w `pwd` --rm --name starter-selenium paterit/starter-selenium pipenv install
	make subl-anaconda-docker
shell:
	@docker exec -it -w `pwd` starter-selenium bash
run:
	@docker exec -it -w `pwd` starter-selenium pipenv run python script.py

subl-anaconda-docker:
	# make sure ~/.config/sublime-text-3/Packages/Anaconda/anaconda_server/docker/start has +x flag set (executable script)
	docker run -d --rm -p 19360:19360 --name starter-selenium \
			-v ~/.config/sublime-text-3/Packages/Anaconda:/opt/anaconda \
			-v `pwd`:`pwd` paterit/starter-selenium \
			/opt/anaconda/anaconda_server/docker/start `pwd`/.venv/bin/python 19360 starter


pipenv-clean:
	sudo rm -rf .venv Pipfile.lock
pipenv-chown:
	sudo chown $(USER):$(USER) -R .venv/ Pipfile Pipfile.lock