PROJECT := earthkit-data
CONDA := conda
CONDAFLAGS :=
COV_REPORT := html

setup:
	pre-commit install

default: qa unit-tests

qa:
	pre-commit run --all-files

unit-tests:
	python -m pytest -vv -m 'not notebook and not no_cache_init' --cov=. --cov-report=$(COV_REPORT)
	python -m pytest -v -m "notebook"
	python -m pytest --forked -vv -m 'no_cache_init'
