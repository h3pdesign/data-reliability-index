# Data Reliability Index

Data Reliability Index is a typed Python SDK for making data trustworthiness explicit before records enter analytics, machine learning, APIs, or databases.

The SDK scores validation evidence, assigns a standardized trust tier, and keeps the original payload linked to reliability metadata. This lets applications reject, quarantine, down-weight, or audit data based on objective criteria instead of implicit assumptions.

## What it provides

- Profile-based scoring for general, scientific, and climate-record data.
- Tiered reliability classification from Tier 1 to Tier 3.
- Policy-based filtering with structured accept/reject decisions.
- Pydantic models for API, database, and message-queue serialization.
- Driver-neutral database helpers for SQL tables and document stores.
- Optional Pandas helpers for analysis pipelines.
- FastAPI examples for ingestion validation.

## Core workflow

1. Collect evidence about completeness, provenance, calibration, schema compliance, anomaly checks, and metadata quality.
2. Use `ReliabilityScanner` to compute a score from `0` to `100`.
3. Assign a trust tier using explicit profile criteria.
4. Enforce a `ReliabilityPolicy` before accepting records into trusted systems.
5. Store the resulting metadata as `dri_*` columns or a nested reliability document.

## Installation

```bash
pip install data-reliability-index
pip install "data-reliability-index[pandas]"
```

Supported Python versions: `3.9` through `3.14`.

For local documentation:

```bash
pip install -e ".[docs]"
mkdocs serve
```
