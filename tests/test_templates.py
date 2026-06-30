import pytest

from data_reliability import (
    DataTier,
    ReliabilityScanner,
    ValidationEvidence,
    climate_record_profile,
    evidence_from_template,
    evidence_templates,
    verified_sensor_template,
)


def test_evidence_templates_registry_contains_common_source_types():
    templates = evidence_templates()

    assert {
        "verified-sensor",
        "trusted-api",
        "cleaned-dataset",
        "user-submission",
        "historical-record",
        "climate-station",
    }.issubset(templates)
    assert isinstance(templates["verified-sensor"].create(), ValidationEvidence)


def test_evidence_template_overrides_known_fields():
    evidence = evidence_from_template(
        "verified-sensor",
        calibration_version="sensor-cal-2026-06",
        notes=["Calibration certificate verified."],
    )

    assert evidence.calibration_version == "sensor-cal-2026-06"
    assert evidence.notes == ["Calibration certificate verified."]
    assert evidence.calibration >= 0.95


def test_evidence_template_rejects_unknown_fields():
    with pytest.raises(ValueError, match="Unknown evidence fields"):
        verified_sensor_template().create(unknown=1.0)


def test_templates_drive_expected_tiers():
    scanner = ReliabilityScanner()

    verified = scanner.scan(
        {"temperature": 21.4, "unit": "celsius"},
        "sensor-a",
        evidence_from_template("verified-sensor"),
    )
    user_submission = scanner.scan(
        {"temperature": 21.4, "unit": "celsius"},
        "form-a",
        evidence_from_template("user-submission"),
    )

    assert verified.reliability.tier == DataTier.TIER_1
    assert user_submission.reliability.tier == DataTier.TIER_3


def test_climate_station_template_matches_climate_record_profile():
    scanner = ReliabilityScanner(profile=climate_record_profile())

    record = scanner.scan(
        {"temperature": 41.7, "unit": "celsius"},
        "station-a",
        evidence_from_template("climate-station"),
    )

    assert record.reliability.tier == DataTier.TIER_1
