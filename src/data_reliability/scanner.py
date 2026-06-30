from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any

from pydantic import BaseModel, Field

from .core import DataTier, ReliableData, ReliabilityMetadata


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
    calibration_version: str | None = None
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


def compute_trace_hash(value: Any, source_id: str) -> str:
    payload = {"source_id": source_id, "value": value}
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


class ReliabilityScanner:
    def __init__(self, weights: ReliabilityWeights | None = None) -> None:
        self.weights = weights or ReliabilityWeights()

    def scan(
        self,
        value: Any,
        source_id: str,
        evidence: ValidationEvidence | None = None,
        *,
        expected_trace_hash: str | None = None,
        required_fields: Sequence[str] | None = None,
    ) -> ReliableData:
        adjusted = self._adjust_evidence(value, source_id, evidence or ValidationEvidence(), expected_trace_hash, required_fields)
        trace_hash = compute_trace_hash(value, source_id)
        score = self.score(adjusted)
        tier = self.assign_tier(score, adjusted)

        metadata = ReliabilityMetadata(
            score=score,
            tier=tier,
            source_id=source_id,
            trace_hash=trace_hash,
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
        if (
            score >= 90
            and evidence.provenance >= 0.9
            and evidence.cryptographic_verification >= 0.9
            and evidence.schema_compliance >= 0.9
            and evidence.timestamp_verified
        ):
            return DataTier.TIER_1
        if score >= 70 and evidence.provenance >= 0.5 and evidence.schema_compliance >= 0.6:
            return DataTier.TIER_2
        return DataTier.TIER_3

    def _adjust_evidence(
        self,
        value: Any,
        source_id: str,
        evidence: ValidationEvidence,
        expected_trace_hash: str | None,
        required_fields: Sequence[str] | None,
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

        if notes != evidence.notes:
            update["notes"] = notes
        if not update:
            return evidence
        return evidence.model_copy(update=update)

    def _missing_fields(self, value: Any, required_fields: Sequence[str]) -> list[str]:
        if not isinstance(value, Mapping):
            return list(required_fields)
        return [field for field in required_fields if field not in value or value[field] is None]
