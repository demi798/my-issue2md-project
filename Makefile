.PHONY: all test install format typecheck lint audit clean

all: test typecheck lint

test:
	pytest tests/ -v --cov=issue2md --cov-report=term-missing

install:
	pip install -e .

format:
	black issue2md tests
	isort issue2md tests

typecheck:
	mypy issue2md

lint:
	ruff check issue2md tests

audit:
	pip-audit

clean:
	rm -rf .pytest_cache .coverage .mypy_cache .ruff_cache out/