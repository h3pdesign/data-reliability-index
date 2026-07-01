# Scientific Use

Data Reliability Index is most useful in scientific workflows when it is treated as an evidence ledger, not as a replacement for domain methodology. It can record whether a data point has enough documented evidence to be used, filtered, down-weighted, or quarantined before analysis.

## Standards Alignment

The SDK is designed to support common expectations from research-data and data-quality practice:

| Practice | How DRI supports it |
| --- | --- |
| FAIR-style reusable data | Stores source identifiers, profile versions, evidence snapshots, and metadata that help downstream systems interpret records. |
| Provenance-aware workflows | Keeps source identifiers, trace hashes, evidence notes, and policy decisions next to the record. |
| Measurement traceability | Separates integrity checks from calibration evidence and stores `calibration_version` when available. |
| Reproducible decisions | Records the scoring profile, profile version, evidence hash, score breakdown inputs, and policy result. |
| Data-quality dimensions | Tracks completeness, consistency, provenance, schema compliance, anomaly checks, duplicate checks, and metadata quality separately. |

Relevant external references include the [FAIR Principles](https://www.go-fair.org/fair-principles/), the [W3C PROV family of provenance standards](https://www.w3.org/TR/prov-overview/), and data-quality standards such as ISO 8000. For measurement-heavy workflows, calibration and uncertainty should follow the relevant metrology or domain standard; DRI records that evidence but does not define it.

## Integrity Is Not Calibration

Scientific records often need several different checks:

- Integrity: the payload has not changed.
- Provenance: the source and processing chain are documented.
- Calibration: the instrument or process is tied to a known reference.
- Plausibility: the value is consistent with domain expectations or comparison data.
- Reproducibility: the scoring profile and evidence can be inspected later.

Trace hashes and HMAC signatures only address integrity and authenticated transport. A record can pass an integrity check and still be scientifically weak if it lacks calibration, provenance, or uncertainty evidence.

For measurement quality, compare observed values against predefined reference or ground-truth values with documented tolerances. See [Reference Comparisons](reference-comparisons.md) for a concrete SDK example.

## Recommended Scientific Workflow

1. Define what each evidence field means for the domain before scoring records.
2. Use a named `ReliabilityProfile` and increment its version when thresholds or weights change.
3. Store reliability metadata with the record, including `evidence_hash` and `evidence_snapshot`.
4. Keep rejected records in quarantine with `decision_to_document()` so rejection reasons remain auditable.
5. Add golden tests for boundary records that must keep stable tier behavior across releases.
6. Treat DRI scores as decision support, not as proof that a scientific claim is true.

## Example Interpretation

A calibrated sensor reading with strong provenance, complete metadata, verified timestamp, and a matching trace hash can reasonably be treated as high-evidence data.

A copied spreadsheet value with no source chain, no calibration context, and no integrity check may still be syntactically valid, but it should receive lower reliability evidence and be excluded or down-weighted by stricter policies.
