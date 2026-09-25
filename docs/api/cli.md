# CLI

## Reference Quality Gates

Store predefined references in a JSON file, for example `references.json`:

```json
[{"field": "temperature", "value": 21.5, "tolerance": 0.2, "reference_id": "lab-v1", "unit": "celsius"}]
```

Apply them to each record in a stream:

```bash
dri scan records.jsonl --jsonl --references references.json --require-reference-checks --fail-on-rejection
```

Reference definitions are loaded once, and JSONL records are processed one at a time. Standard output retains an auditable decision for every processed record. With `--fail-on-rejection`, exit status `1` means at least one record was rejected; without the option, completed scans return `0`. Missing or non-numeric reference fields reject that record and processing continues. Malformed JSON or invalid configuration remains an input error.

Scans without evidence receive zero reliability. Reference agreement alone does not establish provenance, calibration, or timestamp verification; supply justified evidence with `--evidence` and choose thresholds appropriate to the workflow. A shared evidence object applies to every record, so use it only for checks that genuinely apply across that batch.

::: data_reliability.cli
