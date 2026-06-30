from __future__ import annotations

try:
    import pandas as pd
except ImportError:  # pragma: no cover - exercised only when optional dependency is absent
    pd = None  # type: ignore[assignment]

from .core import ReliabilityMetadata, ReliabilityPolicy


def filter_reliable_df(df: pd.DataFrame, policy: ReliabilityPolicy, meta_col: str = "reliability") -> pd.DataFrame:
    """Filter a DataFrame based on a ReliabilityPolicy."""
    if pd is None:
        raise ImportError('Install pandas support with: pip install "data-reliability-index[pandas]"')
    if meta_col not in df.columns:
        raise KeyError(f"DataFrame does not contain reliability metadata column: {meta_col}")

    def check_row(val: object) -> bool:
        if isinstance(val, dict):
            try:
                val = ReliabilityMetadata(**val)
            except ValueError:
                return False
        if not isinstance(val, ReliabilityMetadata):
            return False
        return policy.allows(val)

    mask = df[meta_col].apply(check_row)
    return df[mask].copy()
