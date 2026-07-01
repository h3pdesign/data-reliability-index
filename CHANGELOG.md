# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project follows semantic versioning where practical.

## [0.6.1] - 2026-07-01

### Added

- Reference and ground-truth comparison helpers through `ReferenceValue`, `compare_to_reference()`, `compare_to_references()`, and `evidence_from_reference_comparison()`.
- Aggregated reference quality evidence for multi-field records, mapping predefined reference checks into consistency and anomaly-detection evidence.
- Documentation for scientific use, value-quality checks, and the distinction between payload integrity and measurement quality.

## [0.6.0] - 2026-07-01

### Added

- Score explainability through `ReliabilityScanner.score_breakdown()`.
- Evidence hashes, evidence snapshots, evidence confidence, and uncertainty metadata on scored records.
- SQL and document audit exports for policy decisions through `decision_to_columns()` and `decision_to_document()`.
- Expanded SQL reliability metadata columns for evidence hash, evidence snapshot, confidence, and uncertainty.
- `dri` CLI for scanning JSON and JSONL records.
- Quarantine workflow and external data-quality mapping examples.
- Golden profile tests for default, scientific, and climate-record tier behavior.
- Dependency review workflow for pull requests.
- GitHub artifact attestations for release distributions.
- Documentation for custom profiles, score breakdowns, quarantine workflows, CLI usage, and release provenance.

### Changed

- Updated packaging metadata to include explicit license files with the current setuptools backend baseline.
- Hardened GitHub Actions permissions to least-privilege read access where possible.
- Improved SQL boolean restoration for common database string values.

## [0.5.0] - 2026-06-30

### Added

- Evidence templates for verified sensors, trusted APIs, cleaned datasets, user submissions, historical records, and climate station observations.
- Template registry helpers for creating `ValidationEvidence` without hand-tuning every score.

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
