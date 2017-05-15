ENV ?= pypitest

convert_doc:
	pandoc -f markdown -t rst -o README.txt README.md

build:
	python setup.py sdist

upload:
	python setup.py sdist upload -r $(ENV)
