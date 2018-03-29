ENV ?= pypitest

install:
	pip install -r requirements.txt

venv: requirements.txt
	pip install -r requirements.txt

requirements.txt: requirements.in
	pip-compile requirements.in

update:
	pip-compile -U requirements.in

convert_doc:
	pandoc -f markdown -t rst -o README.txt README.md

build:
	python setup.py sdist

upload:
	python setup.py sdist upload -r $(ENV)

imports:
	find ./src -name '*.py' -print0 | xargs -0 isort -ac -j 8 -l 79 -m 3 -tc -up -fgw 1
	find ./tests -name '*.py' -print0 | xargs -0 isort -ac -j 8 -l 79 -m 3 -tc -up -fgw 1
