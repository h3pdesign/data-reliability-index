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

Before the first publish, configure a PyPI trusted publisher for this project:

- PyPI project name: `data-reliability-index`
- Owner: `h3pdesign`
- Repository name: `data-reliability-index`
- Workflow name: `publish.yml`
- Environment name: `pypi`

To publish a version:

1. Update `version` in `pyproject.toml`.
2. Update `CHANGELOG.md`.
3. Create and push a signed tag, for example `v0.1.0`.
4. Create a GitHub Release from that tag.

The release workflow builds the package, checks it with Twine, creates GitHub artifact attestations for the wheel and source distribution, and publishes to PyPI.

## Release Provenance

The publish workflow uses GitHub OIDC for PyPI trusted publishing and `actions/attest` for release artifact provenance. The attestation binds each artifact in `dist/` to the workflow that produced it, so consumers can verify that the published wheel and source distribution came from this repository's release process.

After a release, verify artifacts with the GitHub CLI:

```bash
gh attestation verify dist/data_reliability_index-<version>-py3-none-any.whl --repo h3pdesign/data-reliability-index
gh attestation verify dist/data_reliability_index-<version>.tar.gz --repo h3pdesign/data-reliability-index
```

Pull requests also run dependency review to block vulnerable package changes at moderate severity or higher.

If PyPI returns `invalid-publisher`, the trusted publisher configuration does not match the GitHub OIDC claims. Recheck the project, owner, repository, workflow, and environment values above, then rerun the failed `Publish` workflow.

## Signed Commits

This repository is configured for SSH commit signing. Local verification uses `.git_allowed_signers`.

Check the latest commit signature with:

```bash
git log --show-signature -1
```
