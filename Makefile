.PHONY: install test lint typecheck audit doctor demo

install:
	python -m pip install -e .

test:
	python -m unittest discover -s tests -v

lint:
	python -m ruff check src tests

typecheck:
	python -m mypy src

audit:
	python -m pip_audit . --skip-editable

doctor:
	python -m nullstate doctor --offline

demo:
	python -m nullstate run examples/azure-public-blob --offline
