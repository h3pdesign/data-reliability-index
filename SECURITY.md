# Security Policy

## Supported Versions

Security fixes are applied to the latest published minor version. Users should upgrade to the newest PyPI release before reporting an issue that may already be fixed.

## Reporting a Vulnerability

Please do not open public GitHub issues for security vulnerabilities.

Report security concerns privately to the repository owner. Include:

- A clear description of the issue.
- Steps to reproduce it.
- The affected version or commit, if known.
- Any practical impact or mitigation you have identified.

The project maintainer will review the report and coordinate a fix before public disclosure when appropriate.

## SDK Security Model

Data Reliability Index helps applications make trust decisions about data quality. It does not replace authentication, authorization, transport security, database permissions, or upstream digital signatures.

Use the SDK with these assumptions:

- Treat all incoming records as untrusted until scanned and accepted by policy.
- Store reliability metadata with the record so downstream systems can audit the decision.
- Use `trace_hash` as an integrity signal for changed payloads, not as proof of source identity.
- Keep `source_id` values stable and non-secret; do not place tokens, passwords, or personal secrets in source identifiers or notes.
- Apply database access controls to both raw records and reliability metadata.
- Prefer signed upstream payloads or authenticated ingestion for high-trust Tier 1 workflows.
