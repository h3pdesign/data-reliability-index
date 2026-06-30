# Release and Publishing

This project publishes Python package artifacts to PyPI and uses GitHub Releases for version announcements.

## Package Artifacts

Build artifacts locally with:

```bash
python -m pip install -e ".[build]"
python -m build
python -m twine check dist/*
```

The expected artifacts are:

- A wheel: `dist/data_reliability_index-<version>-py3-none-any.whl`
- A source distribution: `dist/data_reliability_index-<version>.tar.gz`

## PyPI Publishing

Publishing is handled by `.github/workflows/publish.yml` using PyPI trusted publishing.

To publish a version:

1. Update `version` in `pyproject.toml`.
2. Update `CHANGELOG.md`.
3. Create and push a signed tag, for example `v0.1.0`.
4. Create a GitHub Release from that tag.

The release workflow builds the package, checks it with Twine, and publishes to PyPI.

## Signed Commits

This repository is configured for SSH commit signing. Local verification uses `.git_allowed_signers`.

Check the latest commit signature with:

```bash
git log --show-signature -1
```
