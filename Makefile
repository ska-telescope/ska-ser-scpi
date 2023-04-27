include .make/base.mk
include .make/python.mk

PYTHON_LINE_LENGTH = 88

python-post-lint:
	mypy src/ tests/

.PHONY: docs-pre-build python-post-lint
