# Concepts

## Core idea

Every data point should carry explicit reliability metadata. That metadata can then be used to decide whether the value is admissible for a given study, product feature, or model training run.

The SDK treats reliability as an evidence record, not a one-time label. A score is only useful when downstream systems can inspect which profile produced it, which source identifier was used, whether integrity checks passed, and which policy accepted or rejected the record.

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

Use `ReliabilityScanner.score_breakdown()` when a score needs to be reviewed. It reports each evidence field, normalized weight, weighted contribution, timestamp penalty, uncertainty, and final score.

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

## Evidence templates

Templates are conservative starting points for common source types:

- `verified-sensor`
- `trusted-api`
- `cleaned-dataset`
- `user-submission`
- `historical-record`
- `climate-station`

Use templates to avoid arbitrary all-`1.0` evidence blocks. Override values only when the application can justify the evidence from validation checks, source contracts, signatures, calibration records, or audit metadata.

## Governance alignment

The scoring fields are designed to support practical governance and audit needs:

| Governance expectation | DRI support |
| --- | --- |
| Rich metadata and provenance | `source_id`, `profile_name`, `profile_version`, evidence notes, and document metadata. |
| Integrity and traceability | Deterministic trace hashes plus optional HMAC signature verification. |
| Reproducible decisions | Versioned profiles, explicit tier criteria, and structured policy assessments. |
| Domain standards | Separate profiles for general, scientific, and climate-record data. |
| AI/ML input control | Policy filtering before records are used for model training, evaluation, or inference features. |

These controls complement broader data-management frameworks. They do not replace source-system authentication, access control, calibration programs, model risk management, or domain-specific validation protocols.

## Custom profiles

Teams can define their own `ReliabilityProfile` when the default, scientific, or climate-record profiles do not match the domain. Treat profile changes as methodology changes:

- Give every profile a stable `name` and increment `version` when weights or tier criteria change.
- Define what each evidence field means in the domain before tuning weights.
- Keep Tier 1 thresholds conservative and tied to evidence that can be audited.
- Add golden tests for boundary examples that must keep the same tier over time.
- Store `profile_name`, `profile_version`, `evidence_hash`, and `evidence_snapshot` with accepted records.

Do not tune a profile only to make existing datasets pass. If records are important but weakly evidenced, accept them with a lower tier, quarantine them, or use a policy with explicit lower-confidence treatment.

## Quarantine workflow

Production ingestion should preserve rejected records separately from trusted records. A typical flow is:

1. Scan the input row with source id, evidence, and required fields.
2. Assess the metadata with a `ReliabilityPolicy`.
3. Write accepted rows and metadata to the trusted destination.
4. Write rejected rows, decision reasons, and evidence metadata to quarantine storage.
5. Reprocess quarantined records only after additional evidence is available.

See `examples/quarantine_workflow.py` for a minimal version of this pattern.

## Authenticated integrity

Trace hashes detect whether a payload changed after scanning. They do not prove who produced the payload.

For ingestion systems that share a secret with an upstream producer, use HMAC-SHA256 signatures through `compute_hmac_signature()` and `expected_signature` on `ReliabilityScanner.scan()`. A valid signature can raise `cryptographic_verification` to `1.0`; an invalid or missing secret lowers it to `0.0` and records a note.

For public third-party signatures, verify the provider's signature outside the SDK and then pass the result into `ValidationEvidence`.

## Database storage

For SQL and analytical databases, store `dri_score`, `dri_tier`, `dri_source_id`, `dri_trace_hash`, and timestamp/calibration fields beside the source row. For document databases and object stores, store the reliability metadata as a nested JSON object.

The SDK intentionally does not own database connections or migrations. Applications keep control of their database driver, transactions, indexes, and access permissions while using Data Reliability Index for scoring and policy decisions.

Use `iter_scan_rows()` when processing large datasets so rows can be scored and written in chunks. Use `reliability_columns_ddl()` to generate the reliability columns for SQLite, PostgreSQL, MySQL, or DuckDB.
