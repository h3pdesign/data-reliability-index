# Database Helpers

The database helpers keep the SDK independent from database drivers. They return plain Python dictionaries that can be inserted with SQLite, PostgreSQL, MySQL, DuckDB, warehouse clients, document stores, or message queues.

Recommended SQL columns:

| Column | Meaning |
| --- | --- |
| `dri_score` | Numeric reliability score from 0 to 100. |
| `dri_tier` | Trust tier as `1`, `2`, or `3`. |
| `dri_source_id` | Source identifier used for trace hashing. |
| `dri_trace_hash` | SHA-256 hash of source id and payload. |
| `dri_timestamp_verified` | Whether timestamp integrity was verified. |
| `dri_calibration_version` | Optional calibration reference. |

For document databases, store the full result of `metadata_to_document()` under a nested `reliability` key.

::: data_reliability.database
