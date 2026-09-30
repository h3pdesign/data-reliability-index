import pytest
from data_reliability.core import ReliabilityMetadata, ReliabilityPolicy, DataTier
from data_reliability.scanner import (
    ReliabilityScanner,
    ReliabilityWeights,
    TierCriterion,
    ValidationEvidence,
    climate_record_profile,
    compute_evidence_hash,
    compute_hmac_signature,
    compute_trace_hash,
    scientific_profile,
)
from data_reliability.database import (
    decision_to_columns,
    decision_to_document,
    metadata_from_columns,
    metadata_from_document,
    metadata_to_columns,
    metadata_to_document,
    reliability_column_definitions,
    reliability_columns_ddl,
    scan_row,
    scan_rows,
    trusted_records,
)

def test_policy_allows():
    meta = ReliabilityMetadata(score=95, tier=DataTier.TIER_1, source_id="s1", trace_hash="abc")
    policy = ReliabilityPolicy(minimum_score=90, maximum_tier=DataTier.TIER_2)
    assert policy.allows(meta) is True


@pytest.mark.parametrize("checks", [
    {"expected_trace_hash": "wrong"},
    {"expected_signature": "wrong", "signing_secret": "secret"},
    {"expected_signature": "missing-secret"},
    {"required_fields": ["missing"]},
])
def test_failed_checks_reject_even_under_permissive_policy_after_storage(checks):
    record = ReliabilityScanner().scan(
        {"value": 1}, "lab", ValidationEvidence(calibration=1, cryptographic_verification=1), **checks,
    )
    policy = ReliabilityPolicy(minimum_score=0, maximum_tier=DataTier.TIER_3)
    for metadata in (
        record.reliability,
        metadata_from_columns(metadata_to_columns(record.reliability)),
        metadata_from_document(metadata_to_document(record.reliability)),
    ):
        decision = policy.assess(metadata)
        assert not decision.accepted
        assert not decision.validation_passed
        assert decision.reasons
        assert not decision_to_columns(decision)["dri_decision_validation_passed"]


def test_valid_checks_still_accept():
    value = {"value": 1}
    record = ReliabilityScanner().scan(
        value, "lab", ValidationEvidence(calibration=1),
        required_fields=["value"], expected_trace_hash=compute_trace_hash(value, "lab"),
        expected_signature=compute_hmac_signature(value, "lab", "secret"), signing_secret="secret",
    )
    assert ReliabilityPolicy(minimum_score=90, maximum_tier=DataTier.TIER_1).allows(record.reliability)


@pytest.mark.parametrize("status", [False, 0, "false", "true", 1])
def test_malformed_stored_check_flags_do_not_bypass_policy(status):
    for key in ("reference_checks_passed", "required_fields_passed", "integrity_checks_passed"):
        meta = ReliabilityMetadata(score=100, tier=DataTier.TIER_1, source_id="lab", trace_hash="abc",
                                   evidence_snapshot={key: status})
        assert not ReliabilityPolicy(minimum_score=0, maximum_tier=DataTier.TIER_3).allows(meta)


def test_fast_score_matches_explanation_across_profiles():
    import random
    from data_reliability.scanner import EVIDENCE_FIELDS, default_profile

    rng = random.Random(723)
    for profile in (default_profile(), scientific_profile(), climate_record_profile()):
        scanner = ReliabilityScanner(profile=profile)
        for _ in range(100):
            evidence = ValidationEvidence(
                **{name: rng.random() for name in EVIDENCE_FIELDS}, timestamp_verified=rng.choice([True, False]),
            )
            assert scanner.score(evidence) == scanner.score_breakdown(evidence)["score"]


def test_scan_without_evidence_does_not_invent_quality():
    record = ReliabilityScanner().scan({"temperature": 999}, "unknown")
    assert record.reliability.score == 0
    assert record.reliability.tier == DataTier.TIER_3
    assert record.reliability.timestamp_verified is False


def test_valid_signature_cannot_erase_failed_hash():
    value = {"temperature": 21.4}
    record = ReliabilityScanner().scan(
        value, "lab", expected_trace_hash="incorrect",
        expected_signature=compute_hmac_signature(value, "lab", "secret"),
        signing_secret="secret",
    )
    assert record.reliability.tamper_resistance == 0.0


@pytest.mark.parametrize("value", [-1, 2, float("nan"), float("inf")])
def test_template_overrides_are_validated(value):
    from data_reliability import evidence_from_template

    with pytest.raises(ValueError):
        evidence_from_template("trusted-api", consistency=value)

def test_policy_rejects_low_score():
    meta = ReliabilityMetadata(score=85, tier=DataTier.TIER_1, source_id="s1", trace_hash="abc")
    policy = ReliabilityPolicy(minimum_score=90, maximum_tier=DataTier.TIER_2)
    assert policy.allows(meta) is False

def test_policy_assessment_explains_rejection():
    meta = ReliabilityMetadata(score=85, tier=DataTier.TIER_3, source_id="s1", trace_hash="abc", timestamp_verified=False)
    policy = ReliabilityPolicy(minimum_score=90, maximum_tier=DataTier.TIER_2)

    decision = policy.assess(meta)

    assert decision.accepted is False
    assert decision.score_passed is False
    assert decision.tier_passed is False
    assert decision.timestamp_passed is False
    assert len(decision.reasons) == 3

def test_policy_decision_exports_for_audit_logs():
    meta = ReliabilityMetadata(score=85, tier=DataTier.TIER_3, source_id="s1", trace_hash="abc", timestamp_verified=False)
    policy = ReliabilityPolicy(minimum_score=90, maximum_tier=DataTier.TIER_2)

    decision = policy.assess(meta)
    columns = decision_to_columns(decision)
    document = decision_to_document(decision)

    assert columns["dri_decision_accepted"] is False
    assert columns["dri_decision_maximum_tier"] == 2
    assert "score 85" in columns["dri_decision_reasons"]
    assert document["metadata"]["tier"] == 3

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
    assert reliable.reliability.profile_name == "default"
    assert reliable.reliability.profile_version == "1"
    assert reliable.reliability.trace_hash == compute_trace_hash(value, "sensor-a")
    assert reliable.reliability.evidence_hash == compute_evidence_hash(evidence)
    assert reliable.reliability.evidence_snapshot["calibration_version"] == "sensor-cal-2026-06"
    assert reliable.reliability.evidence_confidence == 1.0
    assert reliable.reliability.uncertainty == 0.0

def test_score_breakdown_explains_contributions_and_penalty():
    scanner = ReliabilityScanner()
    evidence = ValidationEvidence(timestamp_verified=False, cryptographic_verification=1.0)

    breakdown = scanner.score_breakdown(evidence)

    assert breakdown["profile"] == "default"
    assert breakdown["timestamp_penalty_multiplier"] == 0.9
    assert breakdown["fields"]["cryptographic_verification"]["evidence"] == 1.0
    assert breakdown["score"] == scanner.score(evidence)

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

def test_scanner_uses_hmac_signature_verification():
    scanner = ReliabilityScanner()
    value = {"temperature": 21.4}
    signature = compute_hmac_signature(value, "sensor-a", "secret")

    reliable = scanner.scan(
        value,
        "sensor-a",
        ValidationEvidence(cryptographic_verification=0.0),
        expected_signature=signature,
        signing_secret="secret",
    )

    assert reliable.reliability.tamper_resistance == 1.0

def test_scanner_rejects_invalid_hmac_signature():
    scanner = ReliabilityScanner()

    reliable = scanner.scan(
        {"temperature": 21.4},
        "sensor-a",
        ValidationEvidence(cryptographic_verification=1.0),
        expected_signature="invalid",
        signing_secret="secret",
    )

    assert reliable.reliability.tamper_resistance == 0.0
    assert "Signature verification failed." in reliable.reliability.notes

def test_policy_resolves_reliable_data():
    scanner = ReliabilityScanner()
    reliable = scanner.scan({"value": 10}, "api-a", ValidationEvidence(provenance=1.0))
    policy = ReliabilityPolicy(minimum_score=70, maximum_tier=DataTier.TIER_2)

    assert policy.resolve(reliable) == {"value": 10}

def test_policy_filters_reliable_data_batches():
    accepted = ReliabilityScanner().scan({"value": 10}, "api-a", ValidationEvidence(cryptographic_verification=1.0))
    rejected = ReliabilityScanner().scan({"value": 20}, "api-b", ValidationEvidence(completeness=0.1, provenance=0.0))
    policy = ReliabilityPolicy(minimum_score=90, maximum_tier=DataTier.TIER_1)

    assert policy.filter([accepted, rejected]) == [accepted]

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


@pytest.mark.parametrize("value", [-0.1, float("nan"), float("inf"), -float("inf")])
def test_weights_reject_invalid_values(value):
    with pytest.raises(ValueError):
        ReliabilityWeights(consistency=value)


def test_weights_reject_zero_total():
    weights = ReliabilityWeights(**{name: 0.0 for name in ReliabilityWeights.model_fields})
    with pytest.raises(ValueError, match="positive"):
        weights.normalized()


def test_tier_criterion_rejects_nan_threshold():
    with pytest.raises(ValueError, match="thresholds"):
        TierCriterion(minimum_score=90, minimum_evidence={"consistency": float("nan")})

def test_database_column_round_trip():
    meta = ReliabilityMetadata(score=95, tier=DataTier.TIER_1, source_id="sensor-a", trace_hash="abc")

    columns = metadata_to_columns(meta)
    restored = metadata_from_columns(columns)

    assert columns["dri_score"] == 95
    assert columns["dri_profile_name"] == "default"
    assert restored == meta

def test_database_column_round_trip_parses_string_booleans():
    row = {
        "dri_score": 95,
        "dri_tier": 1,
        "dri_source_id": "sensor-a",
        "dri_trace_hash": "abc",
        "dri_timestamp_verified": "false",
    }

    restored = metadata_from_columns(row)

    assert restored.timestamp_verified is False

def test_database_column_round_trip_preserves_evidence_snapshot():
    meta = ReliabilityMetadata(
        score=95,
        tier=DataTier.TIER_1,
        source_id="sensor-a",
        trace_hash="abc",
        evidence_hash="hash",
        evidence_snapshot={"provenance": 1.0},
        evidence_confidence=0.9,
        uncertainty=0.1,
    )

    columns = metadata_to_columns(meta)
    restored = metadata_from_columns(columns)

    assert isinstance(columns["dri_evidence_snapshot"], str)
    assert restored == meta

def test_database_document_round_trip():
    meta = ReliabilityMetadata(score=80, tier=DataTier.TIER_2, source_id="api-a", trace_hash="def")

    document = metadata_to_document(meta)
    restored = metadata_from_document(document)

    assert document["tier"] == 2
    assert restored == meta

def test_scan_row_attaches_reliability_columns():
    row = {"temperature": 21.4, "unit": "celsius"}

    scanned = scan_row(
        row,
        source_id="sensor-a",
        evidence=ValidationEvidence(cryptographic_verification=1.0),
        required_fields=["temperature", "unit"],
    )

    assert scanned["temperature"] == 21.4
    assert scanned["dri_score"] >= 90
    assert scanned["dri_tier"] == 1

def test_scan_rows_scans_iterables_with_source_id_field():
    rows = [{"id": "a", "value": 1}, {"id": "b", "value": 2}]

    scanned = scan_rows(rows, source_id_field="id", evidence=ValidationEvidence(cryptographic_verification=1.0))

    assert [row["dri_source_id"] for row in scanned] == ["a", "b"]
    assert all(row["dri_tier"] == 1 for row in scanned)

def test_reliability_columns_ddl_supports_common_sql_dialects():
    postgres = reliability_column_definitions(dialect="postgres")
    sqlite = reliability_columns_ddl(dialect="sqlite")

    assert postgres["dri_timestamp_verified"] == "BOOLEAN"
    assert "dri_score INTEGER" in sqlite

def test_trusted_records_filters_iterables():
    scanner = ReliabilityScanner()
    accepted = scanner.scan({"value": 10}, "api-a", ValidationEvidence(cryptographic_verification=1.0))
    rejected = scanner.scan({"value": 20}, "api-b", ValidationEvidence(completeness=0.0, provenance=0.0))
    policy = ReliabilityPolicy(minimum_score=90, maximum_tier=DataTier.TIER_1)

    assert trusted_records([accepted, rejected], policy) == [accepted]
