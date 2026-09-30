# Reference Comparisons

Data quality cannot be proven by a hash alone. A hash can show that a payload did not change, but it cannot show that `21.4` is scientifically good, plausible, calibrated, or close to the expected value.

For value quality, define a reference or ground-truth value before scanning the record. That reference can come from a certified instrument, validated lab result, accepted benchmark dataset, domain rule, or quality-controlled historical baseline. The SDK can then compare the observed value against that reference with an explicit tolerance.

## Example

```python
from data_reliability import (
    DataTier,
    ReliabilityPolicy,
    ReliabilityScanner,
    ReferenceValue,
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
            method="predefined acceptance tolerance",
            unit="celsius",
        ),
        ReferenceValue(
            field="humidity",
            value=50.0,
            tolerance=3.0,
            reference_id="lab-humidity-gt",
            source="validated lab baseline",
            method="predefined acceptance tolerance",
            unit="percent",
        ),
    ],
)

evidence = evidence_from_reference_comparison(
    comparison,
    base=ValidationEvidence(
        completeness=1.0,
        provenance=1.0,
        cryptographic_verification=1.0,
        calibration=1.0,
        schema_compliance=1.0,
        metadata_quality=1.0,
        calibration_version="sensor-cal-2026-06",
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
print(reliable.reliability.notes)

policy = ReliabilityPolicy(
    minimum_score=70,
    maximum_tier=DataTier.TIER_3,
    require_reference_checks=True,
)
print(policy.assess(reliable.reliability))
```

This compares observed values with predefined reference values. The tolerances are part of the method and should be chosen from domain knowledge, instrument uncertainty, calibration documents, validation studies, or a documented quality rule.

## What The Index Uses

Reference comparison results become evidence for:

| Evidence field | Meaning |
| --- | --- |
| `consistency` | How close the observed value is to the predefined reference value. |
| `anomaly_detection` | Whether the observed value behaves like an expected value or an outlier. |
| `notes` | The observed value, reference value, tolerance, and pass/fail result. |

Without a supplied `base`, the helper defaults completeness, duplicate detection, provenance, calibration, schema compliance, and metadata quality to zero, and timestamp verification to false. Only consistency and anomaly agreement are derived from the comparison. Supply other evidence from actual checks; reference agreement alone does not establish it. Explicitly constructed `ValidationEvidence` retains legacy defaults for compatibility, so set its fields deliberately.

## Acceptance And Aggregation

The scanner also checks stored absolute error, relative error, and agreement score against its recalculation. Altered derived results cannot be used to inflate evidence while retaining a passing reference status.

Each comparison passes when `abs(observed - reference) <= tolerance`. Inputs must be finite, and tolerance must be positive. Values and tolerances must already use compatible units; the `unit` field is descriptive and performs no conversion. The heuristic agreement score is `1 / (1 + absolute_error / tolerance)`, rounded to four decimal places. It is `1` at exact agreement and `0.5` at the tolerance boundary, not a probability of correctness.

A comparison set reports the arithmetic mean agreement score and passes only when every check passes. When converting a failed set to evidence, consistency and anomaly evidence are capped by the lowest failed comparison score. Passing fields cannot dilute that failure. Applying further comparisons preserves earlier failures and their audit records.

Use `ReliabilityPolicy(require_reference_checks=True, ...)` when reference agreement is mandatory. This rejects missing checks independently of score and tier; known failures are rejected even when the option is off. The option defaults to `False` for workflows without reference checks. The evidence snapshot retains `reference_checks_passed` and structured `reference_comparisons`, including values, tolerances, units, reference IDs, and results, through SQL and document export. The scanner rechecks comparison records against the scanned observation and rejects mismatches or claimed passes without comparison records. The SDK does not authenticate the reference source.

## Ingestion Workflow

Pass references directly to the scanner to compare the actual record at ingestion:

```python
references = [ReferenceValue(field="temperature", value=21.5, tolerance=0.2)]
reliable = ReliabilityScanner().scan(
    {"temperature": 21.4}, source_id="sensor-a", references=references,
)
```

Construct reference definitions once and reuse them across records. Missing or invalid observations produce failed reference evidence with a diagnostic note, allowing ingestion to quarantine those records and continue. No-evidence scans start with score zero and an unverified timestamp. Reference agreement supplies only the dimensions it measures; a strict policy still needs other independently established evidence.

## Good Reference Sources

Use references that are defined before scoring:

| Reference type | Example |
| --- | --- |
| Certified or calibrated measurement | A lab instrument result with a calibration certificate. |
| Domain reference dataset | A validated benchmark or quality-controlled reference table. |
| Historical baseline | A documented range from known-good prior observations. |
| Rule-based reference | A threshold or expected value defined in the study protocol. |

Do not use a reference chosen after seeing the result unless that exploratory step is clearly documented. Otherwise the reliability score can look objective while the method is biased.

## Integrity Versus Value Quality

Use both checks when possible:

| Question | Mechanism |
| --- | --- |
| Did this exact payload change? | `compute_trace_hash`, `expected_trace_hash`, HMAC signatures. |
| Is the value close to predefined references? | `compare_to_references`. |
| Can another person reproduce the decision? | Store `profile_name`, `profile_version`, evidence snapshot, reference, tolerance, and notes. |

The index is strongest when it records all of these signals together. Integrity protects the record from unnoticed change. Reference comparison makes the quality claim explicit.
