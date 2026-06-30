# Data Reliability Index

[![CI](https://github.com/h3pdesign/data-reliability-index/actions/workflows/ci.yml/badge.svg)](https://github.com/h3pdesign/data-reliability-index/actions/workflows/ci.yml)

![Data Reliability Index pipeline visualization](docs/assets/data-reliability-index.png)

Data Reliability Index is a Python package for attaching reliability metadata to data points, enforcing trust policies, and filtering unreliable records before they reach analysis or API boundaries.

The package is built around a simple rule: data should carry the evidence needed to decide whether it is safe to use.

## Release Status

Latest release: [v0.2.0](https://github.com/h3pdesign/data-reliability-index/releases/tag/v0.2.0)

The `v0.2.0` GitHub Release includes signed source, a wheel, and a source distribution. The package is published on PyPI as [`data-reliability-index`](https://pypi.org/project/data-reliability-index/).

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

Install from PyPI:

```bash
pip install data-reliability-index
```

You can also install the latest GitHub Release wheel directly:

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

## How the Data Reliability Index Works

The Data Reliability Index models the complete lifecycle of a data point as it moves from raw input into a trusted dataset. Rather than treating all data equally, the system evaluates, scores, and classifies every record before it becomes eligible for trusted use.

Raw data can enter from APIs, IoT devices, calibrated sensors, databases, files, and user submissions. Because these sources differ in quality and provenance, every incoming record starts as untrusted until it has been analyzed.

The scanning engine evaluates validation evidence for completeness, consistency, provenance, cryptographic verification, calibration, schema compliance, anomaly detection, duplicate detection, and metadata quality. These checks provide an objective assessment of how trustworthy each data point is.

Each scan produces:

- A numeric reliability score from `0` to `100`, representing overall confidence.
- A standardized trust tier from `TIER_1` to `TIER_3`, describing source and verification level.
- A trace hash that can be used to verify whether the data changed.
- A `ReliableData` wrapper containing the original value and its reliability metadata.

Together, the numeric score and trust tier provide more information than either metric alone. The score enables precise filtering and ranking, while the tier gives an immediately understandable description of the data's verification level.

## Trust Tiers

The system classifies data into three standardized trust levels:

| Tier | Trust level | Typical sources | Intended use |
| --- | --- | --- | --- |
| `TIER_1` | Highest trust | Cryptographically verified data, calibrated sensor measurements, direct measurements from trusted APIs | Scientific, safety-critical, and mission-critical applications |
| `TIER_2` | High trust | Cleaned secondary datasets, indirect measurements, partially validated or derived information | Analytics, forecasting, and most production workloads |
| `TIER_3` | Moderate trust | User-generated content, self-reported information, weakly verified external sources | Exploratory analysis and workflows requiring additional validation |

## Intelligent Decision Pipeline

Based on the analysis results, data follows one of two paths:

- Rejected data: records failing minimum reliability requirements are isolated and excluded from trusted datasets.
- Accepted data: records meeting validation thresholds can be stored in trusted repositories while remaining fully traceable.

Every accepted record retains its reliability score, trust tier, provenance metadata, validation evidence, cryptographic integrity information, and audit context. Trust is not only calculated once; it remains transparent and reproducible throughout the data lifecycle.

## Transparent Scoring

The scanner creates a numeric score by applying profile weights to the evidence dimensions. Each evidence value is normalized from `0.0` to `1.0`, multiplied by the active profile's weight, and converted to a `0` to `100` score. Missing timestamps apply an additional penalty when timestamp verification is required.

Trust tiers are then assigned by explicit profile criteria:

- `TIER_1`: the record must pass the Tier 1 minimum score and all required evidence thresholds.
- `TIER_2`: the record must pass the Tier 2 minimum score and all required evidence thresholds.
- `TIER_3`: fallback for records that do not satisfy Tier 1 or Tier 2.

The package includes three profiles:

| Profile | Purpose | Tier behavior |
| --- | --- | --- |
| `default_profile()` | General application, API, and analytics data | Tier 1 requires high score, provenance, cryptographic verification, schema compliance, and verified timestamp |
| `scientific_profile()` | Research data across scientific fields | Increases weight and thresholds for provenance, calibration, consistency, anomaly checks, and reproducibility signals |
| `climate_record_profile()` | Weather and climate record data | Emphasizes calibrated instruments, station metadata, consistency with comparison stations, anomaly checks, and provenance |

The scoring model is stable within a profile. Different use cases change their acceptance thresholds or active profile, not the meaning of reliability itself.

Examples:

- A medical research study may require `TIER_1` data with a score of `99` or higher.
- An autonomous vehicle system may accept only `TIER_1` data above `95`.
- Financial risk models may require `TIER_1` or high-quality `TIER_2` data.
- Product analytics might accept `TIER_2` data with a threshold of `75`.
- Research prototypes may intentionally include `TIER_3` data while applying lower confidence weights.

Because every dataset is evaluated using the same transparent methodology, organizations can define their own acceptance criteria without changing how reliability is measured.

Instead of asking whether a dataset can be trusted, users can inspect objective metrics: reliability score, standardized trust tier, provenance, and validation history.

You can inspect why a record received its tier:

```python
from data_reliability import ReliabilityScanner, ValidationEvidence, climate_record_profile

scanner = ReliabilityScanner(profile=climate_record_profile())
evidence = ValidationEvidence(
    completeness=0.98,
    consistency=0.96,
    provenance=0.96,
    calibration=0.96,
    schema_compliance=0.92,
    anomaly_detection=0.96,
    metadata_quality=0.60,
)

print(scanner.tier_evaluation(evidence))
```

For climate records, this makes methodological uncertainty visible. A temperature record with strong provenance and calibration can still fail Tier 1 if station metadata, anomaly checks, timestamp verification, or comparison-station consistency are insufficient.

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
