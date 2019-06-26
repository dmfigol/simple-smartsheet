.PHONY: black
black:
	poetry run black --check simple_smartsheet

.PHONY: flake8
flake8:
	poetry run flake8 simple_smartsheet

.PHONY: mypy
mypy:
	poetry run mypy simple_smartsheet

.PHONY: examples
examples:
	poetry run python -Werror examples/sheets.py
	poetry run python -Werror examples/report.py
	poetry run python -Werror examples/custom_indexes.py
	poetry run python -Werror examples/async.py

.PHONY: tests
tests: black flake8 mypy examples