from __future__ import annotations

from enum import IntEnum
from typing import Any, List, Optional

from pydantic import BaseModel, Field


class DataTier(IntEnum):
    TIER_1 = 1
    TIER_2 = 2
    TIER_3 = 3


class ReliabilityMetadata(BaseModel):
    score: int = Field(ge=0, le=100, description="Overall reliability score (0-100)")
    tier: DataTier
    source_id: str = Field(min_length=1, max_length=512)
    trace_hash: str = Field(min_length=1, max_length=128)
    profile_name: str = Field(default="default", min_length=1, max_length=128)
    profile_version: str = Field(default="1", min_length=1, max_length=64)
    timestamp_verified: bool = True
    calibration_version: Optional[str] = None
    measurement_accuracy: float = Field(default=1.0, ge=0.0, le=1.0)
    temporal_integrity: float = Field(default=1.0, ge=0.0, le=1.0)
    contextual_consistency: float = Field(default=1.0, ge=0.0, le=1.0)
    methodological_transparency: float = Field(default=1.0, ge=0.0, le=1.0)
    tamper_resistance: float = Field(default=1.0, ge=0.0, le=1.0)
    environmental_stability: float = Field(default=1.0, ge=0.0, le=1.0)
    operator_confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    notes: List[str] = Field(default_factory=list)


class ReliableData(BaseModel):
    value: Any
    reliability: ReliabilityMetadata


class ReliabilityDecision(BaseModel):
    accepted: bool
    score_passed: bool
    tier_passed: bool
    timestamp_passed: bool
    policy: "ReliabilityPolicy"
    metadata: ReliabilityMetadata
    reasons: list[str] = Field(default_factory=list)


class ReliabilityPolicy(BaseModel):
    minimum_score: int = Field(ge=0, le=100)
    maximum_tier: DataTier
    require_timestamp_verified: bool = True

    def assess(self, meta: ReliabilityMetadata) -> ReliabilityDecision:
        score_passed = meta.score >= self.minimum_score
        tier_passed = meta.tier <= self.maximum_tier
        timestamp_passed = meta.timestamp_verified or not self.require_timestamp_verified
        reasons: list[str] = []
        if not score_passed:
            reasons.append(f"score {meta.score} is below required minimum {self.minimum_score}")
        if not tier_passed:
            reasons.append(f"tier {meta.tier.name} is above allowed maximum {self.maximum_tier.name}")
        if not timestamp_passed:
            reasons.append("timestamp verification is required")
        return ReliabilityDecision(
            accepted=score_passed and tier_passed and timestamp_passed,
            score_passed=score_passed,
            tier_passed=tier_passed,
            timestamp_passed=timestamp_passed,
            policy=self,
            metadata=meta,
            reasons=reasons,
        )

    def allows(self, meta: ReliabilityMetadata) -> bool:
        return self.assess(meta).accepted

    def resolve(self, data: ReliableData) -> Optional[Any]:
        if not self.allows(data.reliability):
            return None
        return data.value

    def filter(self, items: list[ReliableData]) -> list[ReliableData]:
        return [item for item in items if self.allows(item.reliability)]
