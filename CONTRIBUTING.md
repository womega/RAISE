# Contributing

Contributions are welcome through pull requests.

Before opening a pull request, run the same validation entry point used for a clean local checkout:

```bash
make ci
```

The target installs the project in editable mode with its development extras before running linting, formatting checks, tests, and the distribution build.

If `make` is unavailable, the equivalent direct commands are:

```bash
python -m pip install -e ".[dev]"
ruff check .
ruff format --check .
pytest
python -m build
```

Please keep public APIs explicit, add tests for behavioural changes, and avoid compatibility-only forwarding modules. Methodological changes that affect rule mining, ranking, masking semantics, or evaluation interpretation should also update the relevant documentation.

Security-sensitive reports should follow `SECURITY.md` rather than being posted as public issues.
