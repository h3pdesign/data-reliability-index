import pytest
from data_reliability.core import ReliabilityMetadata, ReliabilityPolicy, DataTier
from data_reliability.scanner import ReliabilityScanner, ValidationEvidence, compute_trace_hash

def test_policy_allows():
    meta = ReliabilityMetadata(score=95, tier=DataTier.TIER_1, source_id="s1", trace_hash="abc")
    policy = ReliabilityPolicy(minimum_score=90, maximum_tier=DataTier.TIER_2)
    assert policy.allows(meta) is True

def test_policy_rejects_low_score():
    meta = ReliabilityMetadata(score=85, tier=DataTier.TIER_1, source_id="s1", trace_hash="abc")
    policy = ReliabilityPolicy(minimum_score=90, maximum_tier=DataTier.TIER_2)
    assert policy.allows(meta) is False

def test_scanner_assigns_tier_one_for_verified_high_quality_data():
    scanner = ReliabilityScanner()
    value = {"temperature": 21.4, "unit": "celsius"}
    evidence = ValidationEvidence(
        completeness=1.0,
        consistency=1.0,
        provenance=1.0,
        cryptographic_verification=1.0,
        calibration=1.0,
        schema_compliance=1.0,
        anomaly_detection=1.0,
        duplicate_detection=1.0,
        metadata_quality=1.0,
        calibration_version="sensor-cal-2026-06",
    )

    reliable = scanner.scan(value, "sensor-a", evidence)

    assert reliable.value == value
    assert reliable.reliability.score == 100
    assert reliable.reliability.tier == DataTier.TIER_1
    assert reliable.reliability.trace_hash == compute_trace_hash(value, "sensor-a")

def test_scanner_penalizes_missing_required_fields():
    scanner = ReliabilityScanner()

    reliable = scanner.scan(
        {"temperature": 21.4},
        "sensor-a",
        ValidationEvidence(provenance=0.9, schema_compliance=1.0),
        required_fields=["temperature", "unit"],
    )

    assert reliable.reliability.tier == DataTier.TIER_3
    assert reliable.reliability.measurement_accuracy == 0.0
    assert "Missing required fields: unit" in reliable.reliability.notes

def test_scanner_uses_trace_hash_verification():
    scanner = ReliabilityScanner()
    value = {"temperature": 21.4}
    expected_trace_hash = compute_trace_hash(value, "sensor-a")

    reliable = scanner.scan(
        value,
        "sensor-a",
        ValidationEvidence(cryptographic_verification=0.0),
        expected_trace_hash=expected_trace_hash,
    )

    assert reliable.reliability.tamper_resistance == 1.0

def test_policy_resolves_reliable_data():
    scanner = ReliabilityScanner()
    reliable = scanner.scan({"value": 10}, "api-a", ValidationEvidence(provenance=1.0))
    policy = ReliabilityPolicy(minimum_score=70, maximum_tier=DataTier.TIER_2)

    assert policy.resolve(reliable) == {"value": 10}
