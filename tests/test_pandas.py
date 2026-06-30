import pandas as pd
from data_reliability.core import ReliabilityMetadata, ReliabilityPolicy, DataTier
from data_reliability.pandas_ext import filter_reliable_df

def test_pandas_filtering():
    df = pd.DataFrame([
        {"value": 10, "reliability": ReliabilityMetadata(score=95, tier=DataTier.TIER_1, source_id="A", trace_hash="A")},
        {"value": 20, "reliability": ReliabilityMetadata(score=80, tier=DataTier.TIER_2, source_id="B", trace_hash="B")},
        {"value": 30, "reliability": ReliabilityMetadata(score=99, tier=DataTier.TIER_3, source_id="C", trace_hash="C")},
    ])
    policy = ReliabilityPolicy(minimum_score=90, maximum_tier=DataTier.TIER_2)
    filtered = filter_reliable_df(df, policy)
    assert len(filtered) == 1
    assert filtered.iloc[0]["value"] == 10
