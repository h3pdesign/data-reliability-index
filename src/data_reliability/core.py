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
    source_id: str
    trace_hash: str
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

class ReliabilityPolicy(BaseModel):
    minimum_score: int = Field(ge=0, le=100)
    maximum_tier: DataTier
    require_timestamp_verified: bool = True

    def allows(self, meta: ReliabilityMetadata) -> bool:
        if self.require_timestamp_verified and not meta.timestamp_verified:
            return False
        return meta.score >= self.minimum_score and meta.tier <= self.maximum_tier

    def resolve(self, data: ReliableData) -> Any | None:
        if not self.allows(data.reliability):
            return None
        return data.value
