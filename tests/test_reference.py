import pytest

from data_reliability import (
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
