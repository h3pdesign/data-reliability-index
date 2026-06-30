# Evidence Templates

Evidence templates provide conservative starting points for common source types. They are not a substitute for domain review; applications should override any value they can measure directly.

Available templates:

| Template | Intended source |
| --- | --- |
| `verified-sensor` | Direct calibrated sensor data with strong provenance and integrity checks. |
| `trusted-api` | Authenticated provider API data with schema validation. |
| `cleaned-dataset` | Secondary datasets that have been cleaned and partially validated. |
| `user-submission` | User-generated or self-reported records requiring downstream validation. |
| `historical-record` | Historical records with provenance but uncertain instrumentation or metadata. |
| `climate-station` | Calibrated weather or climate station observations. |

Example:

```python
from data_reliability import ReliabilityScanner, evidence_from_template

scanner = ReliabilityScanner()
evidence = evidence_from_template(
    "verified-sensor",
    calibration_version="sensor-cal-2026-06",
)

record = scanner.scan(
    {"temperature": 21.4, "unit": "celsius"},
    source_id="sensor-a",
    evidence=evidence,
)
```

Use `evidence_templates()` to inspect all templates and their default evidence values.

::: data_reliability.templates
