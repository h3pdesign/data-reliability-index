import pytest
from data_reliability.core import ReliabilityMetadata, ReliabilityPolicy, DataTier
from data_reliability.scanner import (
    ReliabilityScanner,
    TierCriterion,
    ValidationEvidence,
    climate_record_profile,
    compute_trace_hash,
    scientific_profile,
)

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

def test_scientific_profile_requires_stronger_evidence_for_tier_one():
    scanner = ReliabilityScanner(profile=scientific_profile())
    evidence = ValidationEvidence(
        completeness=0.98,
        consistency=0.95,
        provenance=0.98,
        cryptographic_verification=0.90,
        calibration=0.95,
        schema_compliance=0.98,
        anomaly_detection=0.95,
        duplicate_detection=0.90,
        metadata_quality=0.90,
    )

    reliable = scanner.scan({"temperature": 21.4, "unit": "celsius"}, "lab-a", evidence)

    assert reliable.reliability.score >= 95
    assert reliable.reliability.tier == DataTier.TIER_1

def test_climate_record_profile_downgrades_weak_station_metadata():
    scanner = ReliabilityScanner(profile=climate_record_profile())
    evidence = ValidationEvidence(
        completeness=0.98,
        consistency=0.96,
        provenance=0.96,
        cryptographic_verification=0.70,
        calibration=0.96,
        schema_compliance=0.92,
        anomaly_detection=0.96,
        duplicate_detection=0.90,
        metadata_quality=0.72,
    )

    reliable = scanner.scan({"temperature": 41.7, "unit": "celsius"}, "station-a", evidence)
    evaluation = scanner.tier_evaluation(evidence)

    assert reliable.reliability.tier == DataTier.TIER_2
    assert evaluation["tier_1"]["allowed"] is False
    assert evaluation["tier_1"]["failed_evidence"]["metadata_quality"]["required"] == 0.85

def test_climate_record_profile_rejects_uncalibrated_extreme_records():
    scanner = ReliabilityScanner(profile=climate_record_profile())
    evidence = ValidationEvidence(
        completeness=0.95,
        consistency=0.80,
        provenance=0.85,
        cryptographic_verification=0.30,
        calibration=0.20,
        schema_compliance=0.90,
        anomaly_detection=0.55,
        duplicate_detection=0.80,
        metadata_quality=0.60,
        notes=["Historical source has unknown radiation shielding."],
    )

    reliable = scanner.scan({"temperature": 42.0, "unit": "celsius"}, "historical-report", evidence)

    assert reliable.reliability.tier == DataTier.TIER_3
    assert reliable.reliability.score < 82

def test_tier_criterion_rejects_unknown_evidence_fields():
    with pytest.raises(ValueError, match="Unknown evidence fields"):
        TierCriterion(minimum_score=90, minimum_evidence={"unknown": 0.9})
