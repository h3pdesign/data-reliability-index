import pytest
from data_reliability.core import ReliabilityMetadata, ReliabilityPolicy, DataTier

def test_policy_allows():
    meta = ReliabilityMetadata(score=95, tier=DataTier.TIER_1, source_id="s1", trace_hash="abc")
    policy = ReliabilityPolicy(minimum_score=90, maximum_tier=DataTier.TIER_2)
    assert policy.allows(meta) is True

def test_policy_rejects_low_score():
    meta = ReliabilityMetadata(score=85, tier=DataTier.TIER_1, source_id="s1", trace_hash="abc")
    policy = ReliabilityPolicy(minimum_score=90, maximum_tier=DataTier.TIER_2)
    assert policy.allows(meta) is False
