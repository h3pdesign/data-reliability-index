from data_reliability import ValidationEvidence


def evidence_from_validation_result(result: dict[str, float | bool]) -> ValidationEvidence:
    """Map external data-quality checks into DRI evidence without adding a dependency."""
    return ValidationEvidence(
        completeness=float(result.get("required_values_present", 0.0)),
        consistency=float(result.get("cross_field_consistency", 0.0)),
        provenance=float(result.get("source_documented", 0.0)),
        schema_compliance=float(result.get("schema_valid", 0.0)),
        anomaly_detection=float(result.get("plausibility_checks_passed", 0.0)),
        duplicate_detection=float(result.get("dedupe_checks_passed", 0.0)),
        metadata_quality=float(result.get("metadata_complete", 0.0)),
        timestamp_verified=bool(result.get("timestamp_verified", False)),
    )
