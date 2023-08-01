include .make/base.mk
include .make/python.mk

# Get rid of these once the pipeline explicitly installs --with dev
python-pre-lint:
	poetry install --with dev

python-pre-test:
	poetry install --with dev

DOCS_SPHINXOPTS = -W --keep-going

PYTHON_LINE_LENGTH = 88

python-post-lint:
	mypy src/ tests/

.PHONY: docs-pre-build python-post-lint
