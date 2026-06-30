import json
import sqlite3

import pandas as pd

from data_reliability import (
    DataTier,
    ReliabilityMetadata,
    ReliabilityPolicy,
    ReliabilityScanner,
    ValidationEvidence,
    filter_reliable_df,
    metadata_from_columns,
    metadata_from_document,
    metadata_to_document,
    scan_row,
)


def high_quality_evidence() -> ValidationEvidence:
    return ValidationEvidence(
        completeness=1.0,
        consistency=1.0,
        provenance=1.0,
        cryptographic_verification=1.0,
        calibration=1.0,
        schema_compliance=1.0,
        anomaly_detection=1.0,
        duplicate_detection=1.0,
        metadata_quality=1.0,
    )


def test_sql_row_document_dataframe_and_sequence_payloads():
    scanner = ReliabilityScanner()
    evidence = high_quality_evidence()
    policy = ReliabilityPolicy(minimum_score=90, maximum_tier=DataTier.TIER_1)

    csv_row = {"id": "r1", "temperature": 21.4, "unit": "celsius"}
    scored_row = scan_row(csv_row, source_id="csv:file", evidence=evidence, required_fields=["temperature", "unit"])
    assert scored_row["dri_score"] == 100
    assert scored_row["dri_tier"] == 1
    assert metadata_from_columns(scored_row).tier == DataTier.TIER_1

    conn = sqlite3.connect(":memory:")
    conn.execute(
        """
        CREATE TABLE readings (
          id TEXT PRIMARY KEY,
          temperature REAL,
          unit TEXT,
          dri_score INTEGER,
          dri_tier INTEGER,
          dri_source_id TEXT,
          dri_trace_hash TEXT,
          dri_profile_name TEXT,
          dri_profile_version TEXT,
          dri_timestamp_verified INTEGER,
          dri_calibration_version TEXT
        )
        """
    )
    conn.execute(
        """
        INSERT INTO readings VALUES (
          :id,
          :temperature,
          :unit,
          :dri_score,
          :dri_tier,
          :dri_source_id,
          :dri_trace_hash,
          :dri_profile_name,
          :dri_profile_version,
          :dri_timestamp_verified,
          :dri_calibration_version
        )
        """,
        scored_row,
    )
    conn.row_factory = sqlite3.Row
    stored = dict(conn.execute("SELECT * FROM readings WHERE id = ?", ("r1",)).fetchone())
    assert policy.allows(metadata_from_columns(stored))

    reliable = scanner.scan({"id": "d1", "sensor": {"value": 21.4}}, "document:collection", evidence)
    document = {"payload": reliable.value, "reliability": metadata_to_document(reliable.reliability)}
    encoded = json.loads(json.dumps(document))
    assert metadata_from_document(encoded["reliability"]).score == 100

    df = pd.DataFrame(
        [
            {"value": 1, "reliability": reliable.reliability},
            {
                "value": 2,
                "reliability": ReliabilityMetadata(score=10, tier=DataTier.TIER_3, source_id="bad", trace_hash="bad"),
            },
        ]
    )
    assert filter_reliable_df(df, policy)["value"].tolist() == [1]

    list_payload = scanner.scan([1, 2, 3], "array:source", evidence)
    assert list_payload.reliability.score == 100

    missing = scanner.scan([1, 2, 3], "array:source", evidence, required_fields=["id"])
    assert missing.reliability.tier == DataTier.TIER_3
