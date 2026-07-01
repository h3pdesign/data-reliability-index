from data_reliability import DataTier, ReliabilityScanner, ValidationEvidence, climate_record_profile, scientific_profile


def test_default_profile_golden_tier_boundaries():
    scanner = ReliabilityScanner()

    tier_1 = scanner.scan(
        {"value": 1},
        "trusted",
        ValidationEvidence(provenance=1.0, cryptographic_verification=1.0, schema_compliance=1.0),
    )
    tier_2 = scanner.scan(
        {"value": 1},
        "partial",
        ValidationEvidence(provenance=0.5, schema_compliance=0.6, cryptographic_verification=0.5, calibration=1.0),
    )
    tier_3 = scanner.scan(
        {"value": 1},
        "weak",
        ValidationEvidence(completeness=0.2, provenance=0.1, schema_compliance=0.2),
    )

    assert tier_1.reliability.tier == DataTier.TIER_1
    assert tier_2.reliability.tier == DataTier.TIER_2
    assert tier_3.reliability.tier == DataTier.TIER_3


def test_scientific_profile_golden_rejects_weak_calibration():
    scanner = ReliabilityScanner(profile=scientific_profile())

    reliable = scanner.scan(
        {"value": 1},
        "lab",
        ValidationEvidence(
            completeness=0.98,
            consistency=0.95,
            provenance=0.98,
            cryptographic_verification=0.90,
            calibration=0.50,
            schema_compliance=0.98,
            anomaly_detection=0.95,
            duplicate_detection=0.90,
            metadata_quality=0.90,
        ),
    )

    assert reliable.reliability.tier == DataTier.TIER_3


def test_climate_record_profile_golden_requires_station_metadata():
    scanner = ReliabilityScanner(profile=climate_record_profile())

    reliable = scanner.scan(
        {"temperature": 41.7, "unit": "celsius"},
        "station",
        ValidationEvidence(
            completeness=0.98,
            consistency=0.96,
            provenance=0.96,
            cryptographic_verification=0.70,
            calibration=0.96,
            schema_compliance=0.92,
            anomaly_detection=0.96,
            duplicate_detection=0.90,
            metadata_quality=0.72,
        ),
    )

    assert reliable.reliability.tier == DataTier.TIER_2
