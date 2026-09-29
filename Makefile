PYTHON ?= python3

.PHONY: help venv install install-dev lint format format-check test build check ci clean

help:
	@printf '%s\n' \
	  'RAISE development commands:' \
	  '  make venv         Create .venv' \
	  '  make install      Install RAISE in editable mode' \
	  '  make install-dev  Install RAISE with development dependencies' \
	  '  make lint         Run Ruff lint checks' \
	  '  make format       Format Python sources with Ruff' \
	  '  make format-check Check formatting without modifying files' \
	  '  make test         Run the test suite' \
	  '  make build        Build sdist and wheel' \
	  '  make check        Run lint, format-check, and tests' \
	  '  make ci           Install development dependencies, then run checks and build' \
	  '  make clean        Remove generated Python/build artifacts'

venv:
	$(PYTHON) -m venv .venv
	@printf '%s\n' 'Activate with: source .venv/bin/activate'

install:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e .

install-dev:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e '.[dev]'

lint:
	$(PYTHON) -m ruff check .

format:
	$(PYTHON) -m ruff format .

format-check:
	$(PYTHON) -m ruff format --check .

test:
	$(PYTHON) -m pytest

build:
	$(PYTHON) -m build

check: lint format-check test

# Keep bootstrap ahead of checks even when callers use make -j.
ci: install-dev
	$(MAKE) check
	$(MAKE) build

clean:
	rm -rf build dist .pytest_cache .ruff_cache .mypy_cache htmlcov .coverage
	find . -type d -name '__pycache__' -prune -exec rm -rf {} +
	find . -type f \( -name '*.pyc' -o -name '*.pyo' \) -delete
	find . -type d -name '*.egg-info' -prune -exec rm -rf {} +
