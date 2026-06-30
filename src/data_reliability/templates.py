from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from .scanner import EVIDENCE_FIELDS, ValidationEvidence


class EvidenceTemplate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    description: str
    evidence: ValidationEvidence

    def create(self, **overrides: Any) -> ValidationEvidence:
        """Create validation evidence from this template with explicit overrides."""
        unknown_fields = sorted(set(overrides) - set(EVIDENCE_FIELDS) - {"timestamp_verified", "calibration_version", "notes"})
        if unknown_fields:
            raise ValueError(f"Unknown evidence fields: {', '.join(unknown_fields)}")
        return self.evidence.model_copy(update=overrides)


def verified_sensor_template() -> EvidenceTemplate:
    return EvidenceTemplate(
        name="verified-sensor",
        description="Direct calibrated sensor measurement with strong provenance and integrity checks.",
        evidence=ValidationEvidence(
            completeness=0.98,
            consistency=0.95,
            provenance=0.95,
            cryptographic_verification=0.90,
            calibration=0.95,
            schema_compliance=0.98,
            anomaly_detection=0.95,
            duplicate_detection=0.90,
            metadata_quality=0.90,
            notes=["Template: verified calibrated sensor measurement."],
        ),
    )


def trusted_api_template() -> EvidenceTemplate:
    return EvidenceTemplate(
        name="trusted-api",
        description="Authenticated API data from a known provider with schema validation.",
        evidence=ValidationEvidence(
            completeness=0.95,
            consistency=0.90,
            provenance=0.95,
            cryptographic_verification=0.85,
            calibration=0.60,
            schema_compliance=0.98,
            anomaly_detection=0.85,
            duplicate_detection=0.90,
            metadata_quality=0.85,
            notes=["Template: trusted authenticated API source."],
        ),
    )


def cleaned_dataset_template() -> EvidenceTemplate:
    return EvidenceTemplate(
        name="cleaned-dataset",
        description="Secondary dataset that has been cleaned, normalized, and partially validated.",
        evidence=ValidationEvidence(
            completeness=0.90,
            consistency=0.85,
            provenance=0.80,
            cryptographic_verification=0.40,
            calibration=0.55,
            schema_compliance=0.92,
            anomaly_detection=0.85,
            duplicate_detection=0.90,
            metadata_quality=0.80,
            notes=["Template: cleaned secondary dataset."],
        ),
    )


def user_submission_template() -> EvidenceTemplate:
    return EvidenceTemplate(
        name="user-submission",
        description="User-generated or self-reported data that needs downstream validation.",
        evidence=ValidationEvidence(
            completeness=0.70,
            consistency=0.45,
            provenance=0.35,
            cryptographic_verification=0.10,
            calibration=0.10,
            schema_compliance=0.75,
            anomaly_detection=0.50,
            duplicate_detection=0.55,
            metadata_quality=0.45,
            notes=["Template: user-submitted or self-reported data."],
        ),
    )


def historical_record_template() -> EvidenceTemplate:
    return EvidenceTemplate(
        name="historical-record",
        description="Historical record with documented provenance but uncertain instrumentation or metadata.",
        evidence=ValidationEvidence(
            completeness=0.80,
            consistency=0.65,
            provenance=0.75,
            cryptographic_verification=0.15,
            calibration=0.35,
            schema_compliance=0.75,
            anomaly_detection=0.60,
            duplicate_detection=0.70,
            metadata_quality=0.60,
            notes=["Template: historical record with higher measurement uncertainty."],
        ),
    )


def climate_station_template() -> EvidenceTemplate:
    return EvidenceTemplate(
        name="climate-station",
        description="Weather or climate station observation with calibrated instrumentation and station metadata.",
        evidence=ValidationEvidence(
            completeness=0.98,
            consistency=0.98,
            provenance=0.98,
            cryptographic_verification=0.85,
            calibration=0.98,
            schema_compliance=0.96,
            anomaly_detection=0.98,
            duplicate_detection=0.95,
            metadata_quality=0.92,
            notes=["Template: calibrated climate station observation."],
        ),
    )


def evidence_templates() -> dict[str, EvidenceTemplate]:
    templates = [
        verified_sensor_template(),
        trusted_api_template(),
        cleaned_dataset_template(),
        user_submission_template(),
        historical_record_template(),
        climate_station_template(),
    ]
    return {template.name: template for template in templates}


def evidence_from_template(name: str, **overrides: Any) -> ValidationEvidence:
    try:
        template = evidence_templates()[name]
    except KeyError as exc:
        supported = ", ".join(sorted(evidence_templates()))
        raise ValueError(f"Unknown evidence template: {name}. Supported templates: {supported}") from exc
    return template.create(**overrides)
