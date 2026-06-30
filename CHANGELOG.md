# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project follows semantic versioning where practical.

## [0.4.0] - 2026-06-30

### Added

- Profile name and version metadata on each scored record.
- HMAC-SHA256 signature helpers for authenticated payload verification.
- Batch and streaming row scanning helpers for larger datasets.
- SQL DDL helpers for SQLite, PostgreSQL, MySQL, and DuckDB reliability columns.
- Optional extras for PostgreSQL, MySQL, DuckDB, MongoDB, Polars, and PyArrow integrations.
- Integration tests for SQL rows, document metadata, DataFrames, row dictionaries, and sequence payloads.

## [0.3.0] - 2026-06-30

### Added

- Explicit tier criteria through `TierCriterion` and `ReliabilityProfile`.
- Default, scientific, and climate-record reliability profiles.
- Tier evaluation diagnostics showing which score or evidence thresholds failed.
- Climate-record scoring criteria for calibrated instruments, provenance, metadata quality, consistency, and anomaly checks.
- Structured `ReliabilityDecision` results for policy audits.
- Driver-neutral database helpers for SQL columns and document-store metadata.

### Changed

- Treat `pandas`, `fastapi`, and `uvicorn` as optional extras so the base package remains a small SDK install.

## [0.2.0] - 2026-06-30

### Added

- Reliability scanning engine for computing scores from validation evidence.
- Automatic trust-tier assignment from score and verification signals.
- Trace hash computation and verification support.
- `ReliableData` wrapper and policy resolution helper.
- Typed API documentation for the scanning engine.

## [0.1.0] - 2026-06-30

### Added

- Initial Data Reliability Index package.
- Pydantic reliability metadata and policy models.
- Pandas filtering helper.
- FastAPI ingestion example.
- MkDocs documentation.
- GitHub repository metadata and CI.
