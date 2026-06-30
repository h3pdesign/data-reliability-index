import pandas as pd
from .core import ReliabilityPolicy, ReliabilityMetadata

def filter_reliable_df(df: pd.DataFrame, policy: ReliabilityPolicy, meta_col: str = "reliability") -> pd.DataFrame:
    '''Filters a DataFrame based on a ReliabilityPolicy.'''
    def check_row(val):
        if isinstance(val, dict):
            try:
                val = ReliabilityMetadata(**val)
            except Exception:
                return False
        if not isinstance(val, ReliabilityMetadata):
            return False
        return policy.allows(val)

    mask = df[meta_col].apply(check_row)
    return df[mask].copy()
