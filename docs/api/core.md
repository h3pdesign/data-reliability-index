# Core Models

## `DataTier`

An integer enum describing the trust level of a data source.

## `ReliabilityMetadata`

A Pydantic model containing the reliability score, tier, and supporting dimensions such as temporal integrity and contextual consistency.

## `ReliabilityPolicy`

A policy object that determines whether a metadata record is acceptable for use.
