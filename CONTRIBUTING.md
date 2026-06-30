# Contributing

Thank you for helping improve Data Reliability Index.

## Development Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[test]"
```

## Tests

Run the existing test suite before opening a pull request:

```bash
pytest
```

## Documentation

Documentation lives in `docs/` and is built with MkDocs Material:

```bash
pip install mkdocs-material
mkdocs serve
```

## Pull Requests

- Keep changes focused.
- Preserve existing behavior unless the change explicitly updates it.
- Add or update tests when changing package behavior.
- Update documentation when public APIs, examples, or workflows change.

By participating in this project, you agree to follow the [Code of Conduct](CODE_OF_CONDUCT.md).
