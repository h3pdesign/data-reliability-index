# API Overview

The SDK exposes four main surfaces:

- `data_reliability.core` for the primary models and policies.
- `data_reliability.scanner` for scoring raw records and assigning trust tiers.
- `data_reliability.database` for driver-neutral SQL and document-store metadata helpers.
- `data_reliability.pandas_ext` for optional DataFrame filtering.
- `data_reliability.cli` for command-line JSON and JSONL scanning.
- `examples.fastapi_app` as a reference integration.

Install optional integrations only when needed:

```bash
pip install "data-reliability-index[pandas]"
pip install "data-reliability-index[api]"
```
