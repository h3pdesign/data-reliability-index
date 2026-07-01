# Database Helpers

The database helpers keep the SDK independent from database drivers. They return plain Python dictionaries that can be inserted with SQLite, PostgreSQL, MySQL, DuckDB, warehouse clients, document stores, or message queues.

Install optional driver stacks only when the application needs them:

```bash
pip install "data-reliability-index[postgres]"
pip install "data-reliability-index[mysql]"
pip install "data-reliability-index[duckdb]"
pip install "data-reliability-index[mongo]"
pip install "data-reliability-index[arrow]"
```

Recommended SQL columns:

| Column | Meaning |
| --- | --- |
| `dri_score` | Numeric reliability score from 0 to 100. |
| `dri_tier` | Trust tier as `1`, `2`, or `3`. |
| `dri_source_id` | Source identifier used for trace hashing. |
| `dri_trace_hash` | SHA-256 hash of source id and payload. |
| `dri_profile_name` | Scoring profile used for the reliability decision. |
| `dri_profile_version` | Profile version used for reproducibility. |
| `dri_evidence_hash` | Hash of the evidence snapshot used for the score. |
| `dri_evidence_snapshot` | JSON evidence snapshot for reproducible audits. |
| `dri_timestamp_verified` | Whether timestamp integrity was verified. |
| `dri_calibration_version` | Optional calibration reference. |
| `dri_evidence_confidence` | Average confidence across evidence dimensions. |
| `dri_uncertainty` | Conservative uncertainty value derived from missing or weak evidence. |

Use `reliability_columns_ddl()` to generate a SQL fragment for SQLite, PostgreSQL, MySQL, or DuckDB.

Use `iter_scan_rows()` for large datasets and `scan_rows()` for small in-memory batches.

For document databases, store the full result of `metadata_to_document()` under a nested `reliability` key.

Use `decision_to_columns()` or `decision_to_document()` when rejected records need an audit trail. These helpers preserve the policy thresholds, pass/fail flags, and rejection reasons alongside the record.

::: data_reliability.database
