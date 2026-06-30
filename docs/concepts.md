# Concepts

## Core idea

Every data point should carry explicit reliability metadata. That metadata can then be used to decide whether the value is admissible for a given study, product feature, or model training run.

## Tiers

- **Tier 1**: Highest confidence data, usually calibrated and directly verified.
- **Tier 2**: Moderately reliable data, often derived or partially validated.
- **Tier 3**: Lowest confidence data, such as self-reported or weakly validated input.

## Policy

A reliability policy defines the minimum score and maximum allowed tier. Data that fails the policy should be excluded automatically.

## Scanning lifecycle

Raw records start as untrusted input. The scanning engine evaluates validation evidence for completeness, consistency, provenance, cryptographic verification, calibration, schema compliance, anomaly checks, duplicate checks, and metadata quality.

The scan produces two outputs:

- A numeric reliability score from 0 to 100.
- A standardized trust tier from Tier 1 to Tier 3.
- The scoring profile name and version used to produce the result.

The score supports precise filtering and ranking. The tier gives downstream users a compact description of the record's verification level.

## Tier criteria

Tier assignment is profile-based. A profile defines:

- Evidence weights for the numeric score.
- Minimum score required for Tier 1 and Tier 2.
- Minimum evidence thresholds that must be met for each tier.
- Whether verified timestamps are required.

The default profile is suitable for general application and analytics data. The scientific profile is stricter for research workflows. The climate-record profile is stricter again for weather and climate records, where calibrated instruments, station metadata, provenance, temporal consistency, and anomaly checks are critical.

Tier 3 is the fallback tier when a record does not satisfy the Tier 1 or Tier 2 criteria. It does not mean the data is useless; it means the data requires additional validation or lower-confidence treatment.

## Scoring evidence

Each evidence field is a normalized value from `0.0` to `1.0`:

| Field | What it measures |
| --- | --- |
| `completeness` | Required values are present and usable. |
| `consistency` | The record agrees with comparison sources or expected context. |
| `provenance` | The source chain is documented and credible. |
| `cryptographic_verification` | Hashes, signatures, or equivalent integrity checks passed. |
| `calibration` | Instruments, processes, or upstream transformations are calibrated and documented. |
| `schema_compliance` | The record satisfies the expected schema and units. |
| `anomaly_detection` | Outlier and plausibility checks passed. |
| `duplicate_detection` | Duplicate or replayed records were checked. |
| `metadata_quality` | Supporting metadata is complete enough to reproduce the trust decision. |

Profiles apply different weights and minimum evidence thresholds to these fields. For example, climate records weight calibration and consistency more heavily than generic application events because station quality, radiation shielding, surroundings, and comparison-station agreement materially affect whether an extreme measurement should be trusted.

## Authenticated integrity

Trace hashes detect whether a payload changed after scanning. They do not prove who produced the payload.

For ingestion systems that share a secret with an upstream producer, use HMAC-SHA256 signatures through `compute_hmac_signature()` and `expected_signature` on `ReliabilityScanner.scan()`. A valid signature can raise `cryptographic_verification` to `1.0`; an invalid or missing secret lowers it to `0.0` and records a note.

For public third-party signatures, verify the provider's signature outside the SDK and then pass the result into `ValidationEvidence`.

## Database storage

For SQL and analytical databases, store `dri_score`, `dri_tier`, `dri_source_id`, `dri_trace_hash`, and timestamp/calibration fields beside the source row. For document databases and object stores, store the reliability metadata as a nested JSON object.

The SDK intentionally does not own database connections or migrations. Applications keep control of their database driver, transactions, indexes, and access permissions while using Data Reliability Index for scoring and policy decisions.

Use `iter_scan_rows()` when processing large datasets so rows can be scored and written in chunks. Use `reliability_columns_ddl()` to generate the reliability columns for SQLite, PostgreSQL, MySQL, or DuckDB.
