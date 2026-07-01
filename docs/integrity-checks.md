# Integrity Checks

An integrity check verifies that a record still matches the payload fingerprint an application expects. It does not prove that the data is true, calibrated, or scientifically valid. It only answers a narrower question: did this exact payload change?

Data Reliability Index supports deterministic trace hashes and HMAC-SHA256 signatures. Trace hashes are useful for detecting changed payloads. HMAC signatures are stronger for authenticated ingestion paths because the producer and consumer share a secret.

## What Is Being Compared

The comparison is not a scientific comparison between two measurements, such as deciding whether `21.4` and `21.5` are close enough. A trace hash compares a candidate record against a previously established fingerprint of the expected record.

That makes it useful for detecting tampering, accidental mutation, replay mistakes, serialization drift, or unexpected source changes. It should not be used as a substitute for calibration, uncertainty analysis, replicate measurements, range checks, or comparison against certified reference data.

## Trace Hash Example

This example compares two records. The first record passes because it matches the original payload used to create the expected hash. The second record fails because the temperature value changed after the expected hash was created.

```python
from data_reliability import ReliabilityScanner, ValidationEvidence, compute_trace_hash

scanner = ReliabilityScanner()

original = {"temperature": 21.4, "unit": "celsius"}
source_id = "sensor-a"

expected_hash = compute_trace_hash(original, source_id)

passed = scanner.scan(
    original,
    source_id=source_id,
    evidence=ValidationEvidence(),
    expected_trace_hash=expected_hash,
)

tampered = {"temperature": 99.9, "unit": "celsius"}

failed = scanner.scan(
    tampered,
    source_id=source_id,
    evidence=ValidationEvidence(),
    expected_trace_hash=expected_hash,
)

print(passed.reliability.tamper_resistance)
print(passed.reliability.notes)

print(failed.reliability.tamper_resistance)
print(failed.reliability.notes)
```

Conceptually:

```text
original record + source_id -> hash A
same record + same source_id -> hash A -> passes

changed record + same source_id -> hash B
hash B does not match hash A -> fails
```

The failed scan sets `tamper_resistance` to `0.0` and adds a note:

```text
Trace hash verification failed.
```

## What This Does Not Prove

A passing trace hash means the payload matches the expected fingerprint. It does not mean:

- the measurement is true
- the instrument was calibrated
- the source is trustworthy
- the record should automatically be accepted by policy

Those questions are represented by other evidence fields, such as provenance, calibration, schema compliance, anomaly checks, timestamp verification, and metadata quality.

## Scientific Use

For scientific workflows, use trace hashes as a chain-of-custody signal rather than a measurement-quality signal. A robust workflow usually separates these questions:

| Question | DRI signal |
| --- | --- |
| Did this payload change after capture or publication? | `trace_hash`, `expected_trace_hash`, `tamper_resistance` |
| Was the source documented? | `provenance` |
| Was the instrument or process calibrated? | `calibration`, `calibration_version` |
| Is the value plausible compared with domain expectations or reference data? | `consistency`, `anomaly_detection` |
| Are required fields, units, and schemas present? | `completeness`, `schema_compliance` |
| Is the decision reproducible later? | `profile_name`, `profile_version`, `evidence_hash`, `evidence_snapshot` |

This aligns with common research-data practices: keep rich metadata, preserve provenance, separate measurement calibration from file or payload integrity, and store enough evidence to reproduce the trust decision. The SDK is not a certification system, but it can make these checks explicit and portable.

## When to Use HMAC

Use HMAC-SHA256 when an upstream producer and downstream consumer share a secret. A valid HMAC signature verifies both payload integrity and that the payload came through an authenticated path controlled by systems that know the secret.
