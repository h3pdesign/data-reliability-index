from __future__ import annotations

import hashlib
import hmac
import json
from collections.abc import Mapping, Sequence
from typing import Any, Optional, Union

from pydantic import BaseModel, Field, field_validator

from .core import DataTier, ReliableData, ReliabilityMetadata

EVIDENCE_FIELDS = (
    "completeness",
    "consistency",
    "provenance",
    "cryptographic_verification",
    "calibration",
    "schema_compliance",
    "anomaly_detection",
    "duplicate_detection",
    "metadata_quality",
)


class ValidationEvidence(BaseModel):
    completeness: float = Field(default=1.0, ge=0.0, le=1.0)
    consistency: float = Field(default=1.0, ge=0.0, le=1.0)
    provenance: float = Field(default=1.0, ge=0.0, le=1.0)
    cryptographic_verification: float = Field(default=0.0, ge=0.0, le=1.0)
    calibration: float = Field(default=0.0, ge=0.0, le=1.0)
    schema_compliance: float = Field(default=1.0, ge=0.0, le=1.0)
    anomaly_detection: float = Field(default=1.0, ge=0.0, le=1.0)
    duplicate_detection: float = Field(default=1.0, ge=0.0, le=1.0)
    metadata_quality: float = Field(default=1.0, ge=0.0, le=1.0)
    timestamp_verified: bool = True
    calibration_version: Optional[str] = None
    notes: list[str] = Field(default_factory=list)


class ReliabilityWeights(BaseModel):
    completeness: float = 0.12
    consistency: float = 0.12
    provenance: float = 0.16
    cryptographic_verification: float = 0.14
    calibration: float = 0.10
    schema_compliance: float = 0.12
    anomaly_detection: float = 0.10
    duplicate_detection: float = 0.06
    metadata_quality: float = 0.08

    def normalized(self) -> dict[str, float]:
        values = self.model_dump()
        total = sum(values.values())
        if total <= 0:
            raise ValueError("Reliability weights must sum to a positive number.")
        return {key: value / total for key, value in values.items()}


class TierCriterion(BaseModel):
    minimum_score: int = Field(ge=0, le=100)
    minimum_evidence: dict[str, float] = Field(default_factory=dict)
    require_timestamp_verified: bool = True
    description: str = ""

    @field_validator("minimum_evidence")
    @classmethod
    def validate_minimum_evidence(cls, value: dict[str, float]) -> dict[str, float]:
        unknown_fields = sorted(set(value) - set(EVIDENCE_FIELDS))
        if unknown_fields:
            raise ValueError(f"Unknown evidence fields: {', '.join(unknown_fields)}")
        invalid = {field: threshold for field, threshold in value.items() if threshold < 0.0 or threshold > 1.0}
        if invalid:
            details = ", ".join(f"{field}={threshold}" for field, threshold in invalid.items())
            raise ValueError(f"Evidence thresholds must be between 0.0 and 1.0: {details}")
        return value

    def allows(self, score: int, evidence: ValidationEvidence) -> bool:
        if score < self.minimum_score:
            return False
        if self.require_timestamp_verified and not evidence.timestamp_verified:
            return False
        values = evidence.model_dump()
        return all(float(values[field]) >= threshold for field, threshold in self.minimum_evidence.items())


class ReliabilityProfile(BaseModel):
    name: str
    description: str
    version: str = "1"
    weights: ReliabilityWeights = Field(default_factory=ReliabilityWeights)
    tier_1: TierCriterion
    tier_2: TierCriterion

    def assign_tier(self, score: int, evidence: ValidationEvidence) -> DataTier:
        if self.tier_1.allows(score, evidence):
            return DataTier.TIER_1
        if self.tier_2.allows(score, evidence):
            return DataTier.TIER_2
        return DataTier.TIER_3


def default_profile() -> ReliabilityProfile:
    return ReliabilityProfile(
        name="default",
        description="General-purpose reliability scoring for API, analytics, and application data.",
        weights=ReliabilityWeights(),
        tier_1=TierCriterion(
            minimum_score=90,
            minimum_evidence={
                "provenance": 0.9,
                "cryptographic_verification": 0.9,
                "schema_compliance": 0.9,
            },
        ),
        tier_2=TierCriterion(
            minimum_score=70,
            minimum_evidence={
                "provenance": 0.5,
                "schema_compliance": 0.6,
            },
            require_timestamp_verified=False,
        ),
    )


def scientific_profile() -> ReliabilityProfile:
    return ReliabilityProfile(
        name="scientific",
        description="Stricter scoring for research data where calibration, provenance, and reproducibility matter.",
        weights=ReliabilityWeights(
            completeness=0.10,
            consistency=0.12,
            provenance=0.18,
            cryptographic_verification=0.12,
            calibration=0.16,
            schema_compliance=0.10,
            anomaly_detection=0.12,
            duplicate_detection=0.04,
            metadata_quality=0.06,
        ),
        tier_1=TierCriterion(
            minimum_score=95,
            minimum_evidence={
                "completeness": 0.95,
                "consistency": 0.90,
                "provenance": 0.95,
                "cryptographic_verification": 0.80,
                "calibration": 0.90,
                "schema_compliance": 0.95,
                "anomaly_detection": 0.90,
                "metadata_quality": 0.85,
            },
        ),
        tier_2=TierCriterion(
            minimum_score=80,
            minimum_evidence={
                "completeness": 0.80,
                "consistency": 0.75,
                "provenance": 0.75,
                "calibration": 0.60,
                "schema_compliance": 0.80,
                "metadata_quality": 0.70,
            },
        ),
    )


def climate_record_profile() -> ReliabilityProfile:
    return ReliabilityProfile(
        name="climate-record",
        description="Scientific profile for weather and climate record data, emphasizing calibrated instruments and station metadata.",
        weights=ReliabilityWeights(
            completeness=0.10,
            consistency=0.15,
            provenance=0.17,
            cryptographic_verification=0.08,
            calibration=0.20,
            schema_compliance=0.08,
            anomaly_detection=0.14,
            duplicate_detection=0.03,
            metadata_quality=0.05,
        ),
        tier_1=TierCriterion(
            minimum_score=96,
            minimum_evidence={
                "completeness": 0.95,
                "consistency": 0.95,
                "provenance": 0.95,
                "calibration": 0.95,
                "schema_compliance": 0.90,
                "anomaly_detection": 0.95,
                "metadata_quality": 0.85,
            },
        ),
        tier_2=TierCriterion(
            minimum_score=82,
            minimum_evidence={
                "completeness": 0.85,
                "consistency": 0.80,
                "provenance": 0.80,
                "calibration": 0.70,
                "schema_compliance": 0.80,
                "anomaly_detection": 0.75,
                "metadata_quality": 0.70,
            },
        ),
    )


def compute_trace_hash(value: Any, source_id: str) -> str:
    payload = {"source_id": source_id, "value": value}
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


SecretValue = Union[str, bytes]


def compute_hmac_signature(value: Any, source_id: str, secret: SecretValue) -> str:
    payload = {"source_id": source_id, "value": value}
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    secret_bytes = secret.encode("utf-8") if isinstance(secret, str) else secret
    return hmac.new(secret_bytes, encoded, hashlib.sha256).hexdigest()


def verify_hmac_signature(value: Any, source_id: str, secret: SecretValue, signature: str) -> bool:
    expected = compute_hmac_signature(value, source_id, secret)
    return hmac.compare_digest(expected, signature)


class ReliabilityScanner:
    def __init__(
        self,
        weights: Optional[ReliabilityWeights] = None,
        profile: Optional[ReliabilityProfile] = None,
    ) -> None:
        selected_profile = profile or default_profile()
        self.profile = selected_profile
        self.weights = weights or selected_profile.weights

    def scan(
        self,
        value: Any,
        source_id: str,
        evidence: Optional[ValidationEvidence] = None,
        *,
        expected_trace_hash: Optional[str] = None,
        expected_signature: Optional[str] = None,
        signing_secret: Optional[SecretValue] = None,
        required_fields: Optional[Sequence[str]] = None,
    ) -> ReliableData:
        adjusted = self._adjust_evidence(
            value,
            source_id,
            evidence or ValidationEvidence(),
            expected_trace_hash,
            expected_signature,
            signing_secret,
            required_fields,
        )
        trace_hash = compute_trace_hash(value, source_id)
        score = self.score(adjusted)
        tier = self.assign_tier(score, adjusted)

        metadata = ReliabilityMetadata(
            score=score,
            tier=tier,
            source_id=source_id,
            trace_hash=trace_hash,
            profile_name=self.profile.name,
            profile_version=self.profile.version,
            timestamp_verified=adjusted.timestamp_verified,
            calibration_version=adjusted.calibration_version,
            measurement_accuracy=adjusted.schema_compliance,
            temporal_integrity=1.0 if adjusted.timestamp_verified else 0.0,
            contextual_consistency=adjusted.consistency,
            methodological_transparency=adjusted.provenance,
            tamper_resistance=adjusted.cryptographic_verification,
            environmental_stability=adjusted.anomaly_detection,
            operator_confidence=adjusted.metadata_quality,
            notes=adjusted.notes,
        )
        return ReliableData(value=value, reliability=metadata)

    def score(self, evidence: ValidationEvidence) -> int:
        weights = self.weights.normalized()
        values = evidence.model_dump()
        weighted = sum(float(values[name]) * weight for name, weight in weights.items())
        if not evidence.timestamp_verified:
            weighted *= 0.9
        return max(0, min(100, round(weighted * 100)))

    def assign_tier(self, score: int, evidence: ValidationEvidence) -> DataTier:
        return self.profile.assign_tier(score, evidence)

    def tier_evaluation(self, evidence: ValidationEvidence) -> dict[str, Any]:
        score = self.score(evidence)
        return {
            "profile": self.profile.name,
            "score": score,
            "tier": self.assign_tier(score, evidence).name,
            "tier_1": self._criterion_status(self.profile.tier_1, score, evidence),
            "tier_2": self._criterion_status(self.profile.tier_2, score, evidence),
        }

    def _adjust_evidence(
        self,
        value: Any,
        source_id: str,
        evidence: ValidationEvidence,
        expected_trace_hash: Optional[str],
        expected_signature: Optional[str],
        signing_secret: Optional[SecretValue],
        required_fields: Optional[Sequence[str]],
    ) -> ValidationEvidence:
        update: dict[str, Any] = {}
        notes = list(evidence.notes)

        if required_fields is not None:
            missing = self._missing_fields(value, required_fields)
            if missing:
                update["completeness"] = min(evidence.completeness, 0.0)
                update["schema_compliance"] = min(evidence.schema_compliance, 0.0)
                notes.append(f"Missing required fields: {', '.join(missing)}")

        if expected_trace_hash is not None:
            actual = compute_trace_hash(value, source_id)
            if actual == expected_trace_hash:
                update["cryptographic_verification"] = max(evidence.cryptographic_verification, 1.0)
            else:
                update["cryptographic_verification"] = min(evidence.cryptographic_verification, 0.0)
                notes.append("Trace hash verification failed.")

        if expected_signature is not None:
            if signing_secret is None:
                update["cryptographic_verification"] = min(evidence.cryptographic_verification, 0.0)
                notes.append("Signature verification failed: signing secret is missing.")
            elif verify_hmac_signature(value, source_id, signing_secret, expected_signature):
                update["cryptographic_verification"] = max(evidence.cryptographic_verification, 1.0)
            else:
                update["cryptographic_verification"] = min(evidence.cryptographic_verification, 0.0)
                notes.append("Signature verification failed.")

        if notes != evidence.notes:
            update["notes"] = notes
        if not update:
            return evidence
        return evidence.model_copy(update=update)

    def _missing_fields(self, value: Any, required_fields: Sequence[str]) -> list[str]:
        if not isinstance(value, Mapping):
            return list(required_fields)
        return [field for field in required_fields if field not in value or value[field] is None]

    def _criterion_status(
        self,
        criterion: TierCriterion,
        score: int,
        evidence: ValidationEvidence,
    ) -> dict[str, Any]:
        values = evidence.model_dump()
        failed_evidence = {
            field: {"actual": float(values[field]), "required": threshold}
            for field, threshold in criterion.minimum_evidence.items()
            if float(values[field]) < threshold
        }
        return {
            "allowed": criterion.allows(score, evidence),
            "minimum_score": criterion.minimum_score,
            "score_passed": score >= criterion.minimum_score,
            "timestamp_passed": evidence.timestamp_verified or not criterion.require_timestamp_verified,
            "failed_evidence": failed_evidence,
        }
