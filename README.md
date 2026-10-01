# Data Reliability Index

<p align="center">
  <img src="docs/assets/data-reliability-index-icon.png" alt="Data Reliability Index icon" width="180">
</p>

[![CI](https://github.com/h3pdesign/data-reliability-index/actions/workflows/ci.yml/badge.svg)](https://github.com/h3pdesign/data-reliability-index/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/data-reliability-index.svg?cacheSeconds=300)](https://pypi.org/project/data-reliability-index/)
[![Python Versions](https://img.shields.io/pypi/pyversions/data-reliability-index.svg)](https://pypi.org/project/data-reliability-index/)
[![License](https://img.shields.io/pypi/l/data-reliability-index.svg)](LICENSE)
[![GitHub Release](https://img.shields.io/github/v/release/h3pdesign/data-reliability-index.svg)](https://github.com/h3pdesign/data-reliability-index/releases)
[![Typed](https://img.shields.io/badge/typed-py.typed-blue.svg)](src/data_reliability/py.typed)

![Data Reliability Index core features infographic](https://raw.githubusercontent.com/h3pdesign/data-reliability-index/main/docs/assets/data-reliability-index-core-features.png)

## Understand the Quality of Your Data Before You Use It

Data Reliability Index is a Python toolkit that helps applications decide whether data meets defined quality requirements before using it in reports, databases, or machine learning.

Imagine a temperature sensor reports **21.4 degrees Celsius**. Is that a good measurement? The number alone cannot tell you. You need a trustworthy reference, an acceptable tolerance, and information about how the measurement was collected.

You could define a reference of **21.5 degrees Celsius**, allowing a difference of **0.2 degrees**. The toolkit checks each measurement against that rule. A reading of 21.4 passes; 28 fails. Missing or invalid measurements are also flagged.

It combines these checks with supplied evidence about things such as calibration, source, completeness, and validation history. Each scanned record receives a **score from 0 to 100** and a quality tier. An acceptance policy then produces an accept-or-reject decision with reasons. Failed required checks cannot be hidden by a high overall score.

This is useful for checking sensor readings, filtering data before analysis, preparing machine-learning datasets, and keeping a traceable explanation of why records were accepted or rejected. It can process records individually or continuously as they arrive.

The important limitation: **it assesses data against the references, rules, and evidence you provide.** It cannot discover the truth by itself. A score of 95 does not mean a 95% chance that a value is correct. Its purpose is to make data-quality decisions explicit, consistent, and inspectable.

Supported Python versions: `3.9` through `3.14`.

## Release Status

Latest release: [v0.7.1](https://github.com/h3pdesign/data-reliability-index/releases/tag/v0.7.1)

The `v0.7.1` release prevents failed integrity and required-field checks from passing policy, verifies derived reference results, and reduces routine scoring overhead. Wheels and source distributions are published on PyPI with artifact provenance attestations by the release workflow.

## Features

- Pydantic models for reliability metadata and policies.
- Scanning engine for computing reliability scores from validation evidence.
- Tiered trust classification with scores from 0 to 100.
- Automatic trust-tier assignment from score and verification signals.
- Trace hash computation and verification support.
- HMAC-SHA256 signature verification for authenticated payload integrity.
- Policy-based acceptance checks for individual records.
- Structured accept/reject decisions for audits and ingestion logs.
- Evidence templates for common source types.
- Driver-neutral database helpers for SQL, analytical, and document stores.
- Batch and streaming row scanning for small files and large datasets.
- Optional Pandas helpers for filtering DataFrames by reliability metadata.
- FastAPI example for rejecting low-reliability input at ingestion time.
- CLI for scanning JSON and JSONL records.
- MkDocs documentation for concepts and API usage.

## Installation

Install from PyPI:

```bash
pip install data-reliability-index
```

Optional integrations:

```bash
pip install "data-reliability-index[pandas]"
pip install "data-reliability-index[api]"
pip install "data-reliability-index[postgres]"
pip install "data-reliability-index[mysql]"
pip install "data-reliability-index[duckdb]"
pip install "data-reliability-index[mongo]"
pip install "data-reliability-index[polars]"
pip install "data-reliability-index[arrow]"
```

To pin the release version:

```bash
pip install data-reliability-index==0.7.1
```

For local development from this repository:

```bash
pip install -e ".[test]"
```

## Quick Start

```python
from data_reliability import (
    DataTier, ReliabilityPolicy, ReliabilityScanner, ValidationEvidence,
    compare_to_reference, evidence_from_reference_comparison,
)

scanner = ReliabilityScanner()
value = {"temperature": 21.4, "unit": "celsius"}
# Define the reference and tolerance before inspecting the observation.
comparison = compare_to_reference(
    value, reference=21.5, tolerance=0.2, field="temperature",
    reference_id="lab-baseline-v1", unit="celsius",
)
evidence = evidence_from_reference_comparison(
    comparison,
    # These illustrative inputs must come from your actual validation checks.
    base=ValidationEvidence(provenance=1.0, calibration=1.0),
)

data = scanner.scan(
    value,
    source_id="sensor-a",
    evidence=evidence,
)

policy = ReliabilityPolicy(
    minimum_score=70,
    maximum_tier=DataTier.TIER_2,
    require_reference_checks=True,
)

assert policy.resolve(data) == {"temperature": 21.4, "unit": "celsius"}
assert policy.assess(data.reliability).accepted is True
```

`require_reference_checks=True` rejects failed or missing reference evidence even when the overall score meets the threshold. Keep each comparison tied to the same observation supplied to `scan()`. See [Reference Comparisons](docs/reference-comparisons.md) for aggregation and audit details.

Failed required-field checks or explicitly requested hash/HMAC checks also reject independently of score and tier. Their outcomes are retained in the evidence snapshot and reported by `decision.validation_passed`. An omitted check is unknown, not a verified pass; legacy snapshots without these fields retain their previous policy behavior.

## How the Data Reliability Index Works

The Data Reliability Index models the complete lifecycle of a data point as it moves from raw input into a trusted dataset. Rather than treating all data equally, the system evaluates, scores, and classifies every record before it becomes eligible for trusted use.

Raw data can enter from APIs, IoT devices, calibrated sensors, databases, files, and user submissions. Because these sources differ in quality and provenance, every incoming record starts as untrusted until it has been analyzed.

The scanning engine combines supplied validation evidence for completeness, consistency, provenance, cryptographic verification, calibration, schema compliance, anomaly detection, duplicate detection, and metadata quality. Reference helpers perform numeric comparisons; the scanner also supports required-field and integrity checks. Other evidence must come from your validators. Default evidence values and templates are assumptions, not proof that checks ran.

Each scan produces:

- A numeric reliability score from `0` to `100`, summarizing evidence under the selected profile.
- A project-defined trust tier from `TIER_1` to `TIER_3`, based on that profile's thresholds.
- A trace hash that can be used to verify whether the data changed.
- The scoring profile name and version used for reproducibility.
- A `ReliableData` wrapper containing the original value and its reliability metadata.

Together, the numeric score and trust tier provide more information than either metric alone. The score enables precise filtering and ranking, while the tier gives an immediately understandable description of the data's verification level.

## Evidence Templates

Templates provide conservative starting points so users do not need to manually set every evidence value for common source types:

- `verified-sensor`
- `trusted-api`
- `cleaned-dataset`
- `user-submission`
- `historical-record`
- `climate-station`

Use templates as defaults and override only values you can justify:

```python
from data_reliability import evidence_from_template

evidence = evidence_from_template(
    "trusted-api",
    cryptographic_verification=1.0,
    notes=["Provider payload signature verified at ingestion."],
)
```

## Trust Tiers

The system classifies data into three profile-defined trust levels. These are not externally certified quality grades:

| Tier | Trust level | Typical sources | Intended use |
| --- | --- | --- | --- |
| `TIER_1` | Highest profile tier | Data meeting the profile's strongest evidence thresholds | Workflows with separately validated domain requirements |
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

Scores are comparable only when the evidence definitions, weights, profile version, and validation methods are compatible. A profile name alone does not establish comparability.

Choose thresholds using representative reference data and assess false acceptance and false rejection on held-out records. A score of `95` does not mean a 95% probability that the observation is correct. The legacy `evidence_confidence` and `uncertainty` fields are the mean evidence value and its complement, not statistical confidence or measurement uncertainty. See [Scientific Use](docs/scientific-use.md) for interpretation and validation requirements.

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

## Authenticated Payloads

For trusted ingestion paths, the SDK can verify an upstream HMAC-SHA256 signature before raising cryptographic evidence:

```python
from data_reliability import ReliabilityScanner, compute_hmac_signature

value = {"temperature": 21.4, "unit": "celsius"}
signature = compute_hmac_signature(value, "sensor-a", "shared-secret")

reliable = ReliabilityScanner().scan(
    value,
    source_id="sensor-a",
    expected_signature=signature,
    signing_secret="shared-secret",
)
```

Use HMAC secrets only for authenticated systems you control. For public third-party signatures, use the provider's signature scheme before passing the result into DRI evidence.

For payload integrity checks, see [Integrity Checks](docs/integrity-checks.md).
For value-quality checks against predefined ground truth or reference values, see [Reference Comparisons](docs/reference-comparisons.md).
For research workflows, see [Scientific Use](docs/scientific-use.md).

## Ground Truth and Reference Checks

For scientific or quality-controlled workflows, define reference values before the data is scored. The index can then show how well observed values match the predefined ground truth, tolerance, source, and method.

```python
from data_reliability import (
    ReferenceValue,
    ReliabilityScanner,
    ValidationEvidence,
    compare_to_references,
    evidence_from_reference_comparison,
    scientific_profile,
)

record = {"temperature": 21.4, "humidity": 48.0, "unit": "metric"}

comparison = compare_to_references(
    record,
    [
        ReferenceValue(
            field="temperature",
            value=21.5,
            tolerance=0.2,
            reference_id="lab-temp-gt",
            source="validated lab baseline",
            unit="celsius",
        ),
        ReferenceValue(
            field="humidity",
            value=50.0,
            tolerance=3.0,
            reference_id="lab-humidity-gt",
            source="validated lab baseline",
            unit="percent",
        ),
    ],
)

evidence = evidence_from_reference_comparison(
    comparison,
    base=ValidationEvidence(
        provenance=1.0,
        calibration=1.0,
        schema_compliance=1.0,
        metadata_quality=1.0,
    ),
)

reliable = ReliabilityScanner(profile=scientific_profile()).scan(
    record,
    source_id="lab-sensor-a",
    evidence=evidence,
)

print(comparison.passed)
print(comparison.quality_score)
print(reliable.reliability.score)
```

This is different from hash verification. Hashes show whether a payload changed. Reference checks show whether values are close enough to predefined quality targets.

## Database Usage

The SDK does not require a database driver. It emits plain dictionaries so the same reliability metadata can be stored in small local databases such as SQLite and DuckDB, production SQL databases such as PostgreSQL and MySQL, analytical warehouses, or document stores.

```python
from data_reliability import ValidationEvidence, scan_row

row = {"temperature": 21.4, "unit": "celsius"}
scored_row = scan_row(
    row,
    source_id="sensor-a",
    evidence=ValidationEvidence(cryptographic_verification=1.0, calibration=1.0),
    required_fields=["temperature", "unit"],
)

assert scored_row["dri_score"] >= 90
assert scored_row["dri_tier"] == 1
```

For large datasets, stream rows instead of materializing everything:

```python
from data_reliability import iter_scan_rows

for scored_row in iter_scan_rows(rows, source_id_field="id", required_fields=["temperature", "unit"]):
    write_to_database(scored_row)
```

Generate reliability column definitions for common SQL engines:

```python
from data_reliability import reliability_columns_ddl

print(reliability_columns_ddl(dialect="postgres"))
```

For SQL tables, store the generated `dri_*` columns beside the source data. For document databases, store `metadata_to_document(reliable.reliability)` as a nested reliability object.

For rejected records, store `decision_to_document(policy.assess(reliable.reliability))` in quarantine or ingestion logs so policy reasons remain auditable.

## CLI Usage

```bash
dri scan records.jsonl --jsonl --source-id-field id --required-field temperature --required-field unit
```

The CLI emits one JSON result per scanned record with the original value, reliability metadata, and policy decision.

## SDK and Security Notes

This project is intended to be used as an SDK. The core package keeps dependencies small, exposes typed Pydantic models, avoids dynamic code execution, and uses deterministic SHA-256 trace hashes to detect changed payloads. Hashes are integrity signals, not proof of source identity by themselves; use authenticated ingestion, HMAC or provider signature verification, database permissions, and private vulnerability reporting for production systems.

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
pip install -e ".[docs]"
mkdocs serve
```

Start with:

- [Concepts](docs/concepts.md)
- [Integrity checks](docs/integrity-checks.md)
- [Scientific use](docs/scientific-use.md)
- [Reference comparisons](docs/reference-comparisons.md)
- [Core models](docs/api/core.md)
- [Scanning engine](docs/api/scanner.md)
- [Evidence templates](docs/api/templates.md)
- [Database helpers](docs/api/database.md)
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
pip install -e ".[api]"
uvicorn examples.fastapi_app:app --reload
```

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for the local workflow and pull request expectations.

## Security

Please report security issues privately. See [SECURITY.md](SECURITY.md).

## License

Licensed under the [Apache License 2.0](LICENSE).
