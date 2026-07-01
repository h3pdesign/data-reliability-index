# Architecture

This diagram shows how Data Reliability Index turns raw records into auditable reliability decisions. The SDK keeps the core scoring path independent from database, API, Pandas, and CLI integrations so applications can adopt the index without changing their storage or ingestion stack.

```mermaid
flowchart TB
    subgraph Inputs["Input surfaces"]
        API["Application / API payloads"]
        Files["JSON, JSONL, CSV-style rows"]
        Sensors["Sensors, labs, stations"]
        Datasets["Existing datasets and warehouses"]
        Users["User submissions"]
    end

    subgraph Evidence["Evidence construction"]
        Templates["Evidence templates<br/>verified-sensor, trusted-api,<br/>cleaned-dataset, user-submission,<br/>historical-record, climate-station"]
        ManualEvidence["Explicit ValidationEvidence<br/>completeness, consistency, provenance,<br/>crypto verification, calibration,<br/>schema compliance, anomaly checks,<br/>duplicate checks, metadata quality"]
        ExternalDQ["External validation results<br/>schema checks, data-quality tools,<br/>domain validation pipelines"]
    end

    subgraph Integrity["Integrity and required-field checks"]
        RequiredFields["Required field validation"]
        TraceHash["Trace hash verification<br/>SHA-256 over source id and payload"]
        HMAC["HMAC-SHA256 signature verification"]
        AdjustedEvidence["Adjusted evidence + notes"]
    end

    subgraph Scoring["Reliability scoring engine"]
        Profile["ReliabilityProfile<br/>default, scientific, climate-record,<br/>or custom domain profile"]
        Weights["Normalized ReliabilityWeights"]
        ScoreBreakdown["score_breakdown()<br/>field contributions, timestamp penalty,<br/>confidence, uncertainty"]
        TierCriteria["TierCriterion checks<br/>minimum score, evidence thresholds,<br/>timestamp requirement"]
        Tier["DataTier<br/>TIER_1, TIER_2, TIER_3"]
    end

    subgraph Metadata["Auditable metadata"]
        ReliableData["ReliableData<br/>original value + reliability metadata"]
        ReliabilityMetadata["ReliabilityMetadata<br/>score, tier, source id, trace hash,<br/>profile name/version, evidence hash,<br/>evidence snapshot, confidence,<br/>uncertainty, notes"]
    end

    subgraph Policy["Policy gate"]
        ReliabilityPolicy["ReliabilityPolicy<br/>minimum score, maximum tier,<br/>timestamp requirement"]
        Decision["ReliabilityDecision<br/>accepted, pass/fail flags,<br/>rejection reasons"]
        Accepted["Accepted trusted record"]
        Quarantine["Rejected / quarantined record"]
    end

    subgraph Outputs["Output and integration surfaces"]
        SQL["SQL / analytical columns<br/>metadata_to_columns()<br/>reliability_columns_ddl()"]
        Docs["Document/object stores<br/>metadata_to_document()<br/>decision_to_document()"]
        Audit["Audit logs<br/>decision_to_columns()<br/>decision_to_document()"]
        Pandas["Pandas filtering<br/>filter_reliable_df()"]
        CLI["CLI<br/>dri scan JSON/JSONL"]
        FastAPI["FastAPI ingestion example"]
    end

    subgraph Release["Project reliability controls"]
        Tests["Unit, integration, CLI,<br/>and golden profile tests"]
        CI["GitHub Actions CI"]
        DependencyReview["Dependency review"]
        Build["Package build + Twine check"]
        Attest["Artifact attestations"]
        PyPI["PyPI trusted publishing"]
    end

    API --> ManualEvidence
    Files --> ManualEvidence
    Sensors --> Templates
    Datasets --> Templates
    Users --> Templates
    ExternalDQ --> ManualEvidence
    Templates --> ManualEvidence

    ManualEvidence --> RequiredFields
    RequiredFields --> TraceHash
    TraceHash --> HMAC
    HMAC --> AdjustedEvidence

    AdjustedEvidence --> Profile
    Profile --> Weights
    Weights --> ScoreBreakdown
    ScoreBreakdown --> TierCriteria
    TierCriteria --> Tier
    Tier --> ReliabilityMetadata
    AdjustedEvidence --> ReliabilityMetadata
    ReliabilityMetadata --> ReliableData

    ReliableData --> ReliabilityPolicy
    ReliabilityPolicy --> Decision
    Decision --> Accepted
    Decision --> Quarantine

    Accepted --> SQL
    Accepted --> Docs
    Accepted --> Pandas
    Accepted --> FastAPI
    Quarantine --> Audit
    CLI --> ManualEvidence
    CLI --> Decision

    Tests --> CI
    CI --> Build
    DependencyReview --> CI
    Build --> Attest
    Attest --> PyPI
```

## Implementation Layers

| Layer | Main modules | Responsibility |
| --- | --- | --- |
| Core models | `data_reliability.core` | Tiers, metadata, reliable payload wrapper, policies, and decisions. |
| Scoring | `data_reliability.scanner` | Evidence models, profiles, score calculation, tier assignment, trace hashes, HMAC verification, and score breakdowns. |
| Templates | `data_reliability.templates` | Conservative evidence defaults for common data source types. |
| Storage helpers | `data_reliability.database` | SQL/document metadata export, DDL generation, row scanning, and decision audit export. |
| Analysis integration | `data_reliability.pandas_ext` | DataFrame filtering by policy. |
| CLI | `data_reliability.cli` | JSON and JSONL record scanning from shell workflows. |
| Examples | `examples/` | FastAPI ingestion, quarantine handling, and external data-quality mapping. |
| Release controls | `.github/workflows/` | CI, dependency review, package publishing, and artifact attestations. |

## Trust Flow

1. Raw data enters through an application, file, data pipeline, API, or manual submission.
2. Evidence is created from a template, explicit validation checks, or external data-quality results.
3. Required fields, trace hashes, and optional HMAC signatures adjust the evidence and add audit notes.
4. The active profile converts evidence into a score, breakdown, confidence, uncertainty, and tier.
5. `ReliabilityPolicy` decides whether the record can enter trusted storage.
6. Accepted records keep metadata beside the value; rejected records keep policy reasons in quarantine or audit logs.
7. Package CI and release provenance controls protect the SDK supply chain that implements the index.
