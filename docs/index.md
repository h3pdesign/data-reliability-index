# Data Reliability Index

Data Reliability Index is a typed Python SDK for making data trustworthiness explicit before records enter analytics, machine learning, APIs, databases, or scientific conclusions.

Many workflows treat measured or collected values as facts even when source quality, calibration, provenance, uncertainty, verification history, or integrity is unknown. The SDK scores validation evidence, assigns a standardized trust tier, and keeps the original payload linked to reliability metadata. This lets applications reject, quarantine, down-weight, or audit data based on objective criteria instead of implicit assumptions.

The goal is to make reliability classification a normal part of data handling. If data points are not classified and verified, downstream analysis can become difficult to reproduce and scientifically weak because the trust level of the underlying evidence was never made explicit.

The model is intended to complement established data-governance practices: rich metadata, persistent source identifiers, documented provenance, reproducible scoring profiles, and explicit policy gates. In AI or machine-learning workflows, the same metadata helps teams separate high-confidence inputs from records that need quarantine, down-weighting, or additional review before they influence models.

## What it provides

- Profile-based scoring for general, scientific, and climate-record data.
- Evidence templates for common source types.
- Tiered reliability classification from Tier 1 to Tier 3.
- Policy-based filtering with structured accept/reject decisions.
- Pydantic models for API, database, and message-queue serialization.
- Driver-neutral database helpers for SQL tables and document stores.
- Streaming row scanning and SQL DDL generation for database pipelines.
- HMAC-SHA256 verification for authenticated ingestion systems.
- Optional Pandas helpers for analysis pipelines.
- FastAPI examples for ingestion validation.
- Release provenance controls for package artifacts.
- A small `dri` CLI for scanning JSON and JSONL files.

## Core workflow

1. Collect evidence about completeness, provenance, calibration, schema compliance, anomaly checks, and metadata quality, or start from an evidence template.
2. Use `ReliabilityScanner` to compute a score from `0` to `100`.
3. Assign a trust tier using explicit profile criteria.
4. Enforce a `ReliabilityPolicy` before accepting records into trusted systems.
5. Store the resulting metadata, profile name, and profile version as `dri_*` columns or a nested reliability document.

## Reliability standards fit

Data Reliability Index does not claim to certify datasets. It gives applications a consistent way to record evidence that supports common governance expectations:

- Findable and reusable records need stable identifiers, rich metadata, provenance, and domain-relevant standards.
- AI and analytics pipelines need data-quality signals that are valid, reliable, transparent, traceable, and auditable.
- Production ingestion paths need integrity checks, explicit acceptance policy, and reproducible scoring versions.

## Command line usage

The package installs a `dri` command for local files and pipeline smoke tests:

```bash
dri scan records.jsonl --jsonl --source-id-field id --required-field temperature --required-field unit
```

Each output line contains the original value, reliability metadata, and policy decision. Use it to inspect datasets before writing ingestion code.

For a complete implementation overview, see the [Architecture](architecture.md) diagram.

## Installation

```bash
pip install data-reliability-index
pip install "data-reliability-index[pandas]"
pip install "data-reliability-index[postgres]"
```

Supported Python versions: `3.9` through `3.14`.

For local documentation:

```bash
pip install -e ".[docs]"
mkdocs serve
```
