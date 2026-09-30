import pytest

from data_reliability import (
    DataTier,
    ReliabilityPolicy,
    ReliabilityScanner,
    ReferenceValue,
    ValidationEvidence,
    compare_to_reference,
    compare_to_references,
    evidence_from_reference_comparison,
    scientific_profile,
)


def test_reference_comparison_passes_within_predefined_tolerance():
    comparison = compare_to_reference(
        {"temperature": 21.4},
        reference=21.5,
        tolerance=0.2,
        field="temperature",
    )

    assert comparison.passed is True
    assert comparison.absolute_error == pytest.approx(0.1)
    assert comparison.relative_error == pytest.approx(0.1 / 21.5)
    assert comparison.quality_score == pytest.approx(0.6667)


def test_reference_comparison_fails_outside_predefined_tolerance():
    comparison = compare_to_reference(
        {"temperature": 99.9},
        reference=21.4,
        tolerance=0.5,
        field="temperature",
    )
    evidence = evidence_from_reference_comparison(
        comparison,
        base=ValidationEvidence(provenance=1.0, calibration=1.0, schema_compliance=1.0),
    )

    assert comparison.passed is False
    assert comparison.quality_score < 0.01
    assert evidence.consistency == comparison.quality_score
    assert evidence.anomaly_detection == comparison.quality_score
    assert "Reference comparison failed for temperature" in evidence.notes[-1]


def test_reference_evidence_feeds_the_scientific_scanner():
    comparison = compare_to_reference(
        {"temperature": 21.4, "unit": "celsius"},
        reference=21.4,
        tolerance=0.2,
        field="temperature",
    )
    evidence = evidence_from_reference_comparison(
        comparison,
        base=ValidationEvidence(
            completeness=1.0,
            provenance=1.0,
            cryptographic_verification=1.0,
            calibration=1.0,
            schema_compliance=1.0,
            metadata_quality=1.0,
        ),
    )

    reliable = ReliabilityScanner(profile=scientific_profile()).scan(
        {"temperature": 21.4, "unit": "celsius"},
        source_id="lab-sensor-a",
        evidence=evidence,
    )

    assert reliable.reliability.contextual_consistency == 1.0
    assert reliable.reliability.environmental_stability == 1.0
    assert reliable.reliability.score >= 95


def test_multiple_predefined_references_create_aggregate_quality_evidence():
    record = {"temperature": 21.6, "humidity": 48.0}
    result = compare_to_references(
        record,
        [
            ReferenceValue(
                field="temperature",
                value=21.5,
                tolerance=0.2,
                reference_id="lab-temp-gt",
                source="validated lab baseline",
                unit="celsius",
            ),
            ReferenceValue(
                field="humidity",
                value=50.0,
                tolerance=3.0,
                reference_id="lab-humidity-gt",
                source="validated lab baseline",
                unit="percent",
            ),
        ],
    )
    evidence = evidence_from_reference_comparison(result)

    assert result.passed is True
    assert len(result.comparisons) == 2
    assert 0.0 < result.quality_score < 1.0
    assert evidence.consistency == result.quality_score
    assert evidence.anomaly_detection == result.quality_score
    assert "Reference set passed." in evidence.notes[-1]


@pytest.mark.parametrize("invalid", [float("nan"), float("inf"), -float("inf"), True])
@pytest.mark.parametrize("argument", ["value", "reference", "tolerance"])
def test_reference_rejects_nonfinite_and_boolean_inputs(invalid, argument):
    arguments = {"value": 1.0, "reference": 1.0, "tolerance": 0.5}
    arguments[argument] = invalid
    with pytest.raises(ValueError, match="finite number"):
        compare_to_reference(**arguments)


@pytest.mark.parametrize("field", ["value", "tolerance"])
def test_reference_definition_rejects_infinity(field):
    arguments = {"field": "temperature", "value": 1.0, "tolerance": 0.5}
    arguments[field] = float("inf")
    with pytest.raises(ValueError):
        ReferenceValue(**arguments)


def test_failed_reference_is_not_diluted_by_successful_fields():
    result = compare_to_references(
        {"bad": 100.0, "good": 0.0},
        [ReferenceValue(field=name, value=0.0, tolerance=1.0) for name in ["bad", "good"]],
    )
    evidence = evidence_from_reference_comparison(result)
    assert result.quality_score > 0.5
    assert evidence.consistency == result.comparisons[0].quality_score
    assert evidence.anomaly_detection == result.comparisons[0].quality_score
    assert evidence.reference_checks_passed is False


def test_reference_agreement_does_not_invent_other_evidence():
    evidence = evidence_from_reference_comparison(compare_to_reference(1, 1, tolerance=0.5))
    assert evidence.provenance == 0.0
    assert evidence.calibration == 0.0
    assert evidence.schema_compliance == 0.0
    assert evidence.metadata_quality == 0.0


def test_later_reference_success_cannot_erase_failure():
    failed = evidence_from_reference_comparison(compare_to_reference(10, 1, tolerance=0.5))
    combined = evidence_from_reference_comparison(compare_to_reference(1, 1, tolerance=0.5), base=failed)
    assert combined.reference_checks_passed is False
    assert len(combined.reference_comparisons) == 2
    assert combined.consistency == failed.consistency


@pytest.mark.parametrize("observed,accepted", [(1.0, True), (2.0, False)])
def test_reference_policy_survives_sql_and_document_storage(observed, accepted):
    from data_reliability.database import (
        metadata_from_columns, metadata_to_columns,
        metadata_from_document, metadata_to_document, decision_to_columns,
    )

    evidence = evidence_from_reference_comparison(
        compare_to_reference(observed, 1.0, tolerance=0.5),
        base=ValidationEvidence(timestamp_verified=True),
    )
    record = ReliabilityScanner().scan(observed, "lab", evidence)
    policy = ReliabilityPolicy(minimum_score=0, maximum_tier=DataTier.TIER_3, require_reference_checks=True)
    for metadata in [record.reliability,
                     metadata_from_columns(metadata_to_columns(record.reliability)),
                     metadata_from_document(metadata_to_document(record.reliability))]:
        decision = policy.assess(metadata)
        assert decision.accepted is accepted
        assert decision.reference_passed is accepted
        assert decision_to_columns(decision)["dri_decision_reference_passed"] is accepted
        assert metadata.evidence_snapshot["reference_comparisons"][0]["observed"] == observed


def test_reference_policy_rejects_missing_checks_even_with_perfect_score():
    record = ReliabilityScanner().scan(1, "lab", ValidationEvidence(calibration=1, cryptographic_verification=1))
    assert record.reliability.score == 100
    policy = ReliabilityPolicy(minimum_score=90, maximum_tier=DataTier.TIER_1, require_reference_checks=True)
    decision = policy.assess(record.reliability)
    assert not decision.accepted
    assert "reference checks" in decision.reasons[0]


def test_reference_tolerance_boundary_is_inclusive():
    assert compare_to_reference(1.5, 1, tolerance=0.5).passed
    assert not compare_to_reference(1.500001, 1, tolerance=0.5).passed


def test_scanner_rejects_inflated_comparison_quality():
    comparison = compare_to_reference(1.25, 1, tolerance=0.5)
    comparison.quality_score = 1.0
    evidence = evidence_from_reference_comparison(comparison)
    record = ReliabilityScanner().scan(1.25, "lab", evidence)
    assert record.reliability.evidence_snapshot["reference_checks_passed"] is False


@pytest.mark.parametrize("value", [2.0, None, True, float("nan")])
def test_scanner_rejects_reused_reference_evidence(value):
    evidence = evidence_from_reference_comparison(compare_to_reference(1.0, 1.0, tolerance=0.5))
    record = ReliabilityScanner().scan(value, "lab", evidence)
    policy = ReliabilityPolicy(minimum_score=0, maximum_tier=DataTier.TIER_3, require_timestamp_verified=False)
    assert record.reliability.evidence_snapshot["reference_checks_passed"] is False
    assert not policy.allows(record.reliability)


def test_scanner_rejects_reference_pass_without_comparison_records():
    record = ReliabilityScanner().scan(1, "lab", ValidationEvidence(reference_checks_passed=True))
    assert record.reliability.evidence_snapshot["reference_checks_passed"] is False


@pytest.mark.parametrize("field", ["value", "tolerance"])
def test_reference_definition_rejects_booleans(field):
    arguments = {"field": "temperature", "value": 1, "tolerance": 0.5}
    arguments[field] = True
    with pytest.raises(ValueError):
        ReferenceValue(**arguments)


def test_empty_reference_set_cannot_create_passing_evidence():
    from data_reliability import ReferenceComparisonSet

    comparison = ReferenceComparisonSet(comparisons=[], passed=True, quality_score=1)
    with pytest.raises(ValueError, match="at least one"):
        evidence_from_reference_comparison(comparison)
