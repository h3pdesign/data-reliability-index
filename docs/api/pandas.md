# Pandas Extension

## `filter_reliable_df`

Filters a DataFrame by applying a `ReliabilityPolicy` to the metadata column.

```python
filtered = filter_reliable_df(df, policy, meta_col="reliability")
```
