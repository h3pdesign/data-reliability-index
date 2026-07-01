# Reference Comparisons

Data quality cannot be proven by a hash alone. A hash can show that a payload did not change, but it cannot show that `21.4` is scientifically good, plausible, calibrated, or close to the expected value.

For value quality, define a reference or ground-truth value before scanning the record. That reference can come from a certified instrument, validated lab result, accepted benchmark dataset, domain rule, or quality-controlled historical baseline. The SDK can then compare the observed value against that reference with an explicit tolerance.

## Example

```python
from data_reliability import (
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
```

This compares observed values with predefined reference values. The tolerances are part of the method and should be chosen from domain knowledge, instrument uncertainty, calibration documents, validation studies, or a documented quality rule.

## What The Index Uses

Reference comparison results become evidence for:

| Evidence field | Meaning |
| --- | --- |
| `consistency` | How close the observed value is to the predefined reference value. |
| `anomaly_detection` | Whether the observed value behaves like an expected value or an outlier. |
| `notes` | The observed value, reference value, tolerance, and pass/fail result. |

The helper does not silently set provenance, calibration, or schema evidence. Those must still come from the surrounding workflow. A value can be close to a reference but still have weak provenance, missing calibration, or incomplete metadata.

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
