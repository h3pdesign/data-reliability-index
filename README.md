# Data Reliability Index

[![CI](https://github.com/h3pdesign/data-reliability-index/actions/workflows/ci.yml/badge.svg)](https://github.com/h3pdesign/data-reliability-index/actions/workflows/ci.yml)

![Data Reliability Index pipeline visualization](docs/assets/data-reliability-index.png)

Data Reliability Index is a Python package for attaching reliability metadata to data points, enforcing trust policies, and filtering unreliable records before they reach analysis or API boundaries.

The package is built around a simple rule: data should carry the evidence needed to decide whether it is safe to use.

## Features

- Pydantic models for reliability metadata and policies.
- Tiered trust classification with scores from 0 to 100.
- Policy-based acceptance checks for individual records.
- Pandas helpers for filtering DataFrames by reliability metadata.
- FastAPI example for rejecting low-reliability input at ingestion time.
- MkDocs documentation for concepts and API usage.

## Installation

```bash
pip install data-reliability-index
```

For local development from this repository:

```bash
pip install -e ".[test]"
```

## Quick Start

```python
from data_reliability import DataTier, ReliabilityMetadata, ReliabilityPolicy

metadata = ReliabilityMetadata(
    score=95,
    tier=DataTier.TIER_1,
    source_id="sensor-a",
    trace_hash="abc123",
)

policy = ReliabilityPolicy(
    minimum_score=90,
    maximum_tier=DataTier.TIER_2,
)

assert policy.allows(metadata) is True
```

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
- [Pandas extension](docs/api/pandas.md)
- [FastAPI example](docs/api/fastapi.md)

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
