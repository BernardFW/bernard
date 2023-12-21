ENV ?= pypitest

install:
	poetry install

update:
	poetry update

build:
	poetry build

upload:
	twine upload dist/*

format:
	poetry run isort .
	poetry run black .
