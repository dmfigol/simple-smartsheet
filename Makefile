.PHONY: black
black:
	poetry run black --check simple_smartsheet examples tests

.PHONY: flake8
flake8:
	poetry run flake8 simple_smartsheet examples tests

.PHONY: mypy
mypy:
	poetry run mypy simple_smartsheet

.PHONY: pytest
pytest:
	poetry run pytest --record-mode=none --block-network

.PHONY: pytest-integration
pytest-integration:
	poetry run pytest --record-mode=all --prod

.PHONY: examples
examples:
	poetry run python -Werror examples/sheets.py > /dev/null
	poetry run python -Werror examples/report.py > /dev/null
	poetry run python -Werror examples/custom_indexes.py > /dev/null
	poetry run python -Werror examples/async.py > /dev/null

.PHONY: tests
tests: black flake8 mypy pytest

.PHONY: tests-ci
tests-ci: black flake8 mypy pytest-integration examples
