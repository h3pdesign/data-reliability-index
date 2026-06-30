# Data Reliability Index

[![CI](https://github.com/h3pdesign/data-reliability-index/actions/workflows/ci.yml/badge.svg)](https://github.com/h3pdesign/data-reliability-index/actions/workflows/ci.yml)

![Data Reliability Index pipeline visualization](docs/assets/data-reliability-index.png)

Data Reliability Index is a Python package for attaching reliability metadata to data points, enforcing trust policies, and filtering unreliable records before they reach analysis or API boundaries.

The package is built around a simple rule: data should carry the evidence needed to decide whether it is safe to use.

## Release Status

Latest release: [v0.2.0](https://github.com/h3pdesign/data-reliability-index/releases/tag/v0.2.0)

The `v0.2.0` GitHub Release includes signed source, a wheel, and a source distribution. PyPI publishing is configured through GitHub Actions.

## Features

- Pydantic models for reliability metadata and policies.
- Scanning engine for computing reliability scores from validation evidence.
- Tiered trust classification with scores from 0 to 100.
- Automatic trust-tier assignment from score and verification signals.
- Trace hash computation and verification support.
- Policy-based acceptance checks for individual records.
- Pandas helpers for filtering DataFrames by reliability metadata.
- FastAPI example for rejecting low-reliability input at ingestion time.
- MkDocs documentation for concepts and API usage.

## Installation

From PyPI, once publishing is enabled:

```bash
pip install data-reliability-index
```

Until then, install the latest GitHub Release wheel directly:

```bash
pip install https://github.com/h3pdesign/data-reliability-index/releases/download/v0.2.0/data_reliability_index-0.2.0-py3-none-any.whl
```

For local development from this repository:

```bash
pip install -e ".[test]"
```

## Quick Start

```python
from data_reliability import DataTier, ReliabilityPolicy, ReliabilityScanner, ValidationEvidence

scanner = ReliabilityScanner()
data = scanner.scan(
    {"temperature": 21.4, "unit": "celsius"},
    source_id="sensor-a",
    evidence=ValidationEvidence(
        completeness=1.0,
        consistency=1.0,
        provenance=1.0,
        cryptographic_verification=1.0,
        calibration=1.0,
        schema_compliance=1.0,
        anomaly_detection=1.0,
        duplicate_detection=1.0,
        metadata_quality=1.0,
    ),
)

policy = ReliabilityPolicy(
    minimum_score=90,
    maximum_tier=DataTier.TIER_2,
)

assert policy.resolve(data) == {"temperature": 21.4, "unit": "celsius"}
```

## Pipeline Model

Raw data starts as untrusted input. The scanner evaluates validation evidence for completeness, consistency, provenance, cryptographic verification, calibration, schema compliance, anomaly detection, duplicate detection, and metadata quality.

Each scan produces:

- A numeric reliability score from `0` to `100`.
- A standardized trust tier from `TIER_1` to `TIER_3`.
- A trace hash that can be used to verify whether the data changed.
- A `ReliableData` wrapper containing the original value and its reliability metadata.

## Pandas Filtering

```python
import pandas as pd
from data_reliability import DataTier, ReliabilityMetadata, ReliabilityPolicy, filter_reliable_df

df = pd.DataFrame([
    {
        "value": 10,
        "reliability": ReliabilityMetadata(
            score=95,
            tier=DataTier.TIER_1,
            source_id="sensor-a",
            trace_hash="abc123",
        ),
    },
])

policy = ReliabilityPolicy(minimum_score=90, maximum_tier=DataTier.TIER_2)
trusted = filter_reliable_df(df, policy)
```

## Documentation

The project documentation lives in [`docs/`](docs/) and can be served locally with MkDocs:

```bash
pip install mkdocs-material
mkdocs serve
```

Start with:

- [Concepts](docs/concepts.md)
- [Core models](docs/api/core.md)
- [Scanning engine](docs/api/scanner.md)
- [Pandas extension](docs/api/pandas.md)
- [FastAPI example](docs/api/fastapi.md)
- [Release and publishing](docs/release.md)

The longer project rationale is available in [`data-reliability.md`](data-reliability.md).

## Development

Run the test suite:

```bash
pip install -e ".[test]"
pytest
```

Build package artifacts:

```bash
pip install -e ".[build]"
python -m build
python -m twine check dist/*
```

Run the FastAPI example:

```bash
uvicorn examples.fastapi_app:app --reload
```

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for the local workflow and pull request expectations.

## Security

Please report security issues privately. See [SECURITY.md](SECURITY.md).

## License

Licensed under the [Apache License 2.0](LICENSE).
