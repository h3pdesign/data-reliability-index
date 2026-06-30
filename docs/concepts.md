# Concepts

## Core idea

Every data point should carry explicit reliability metadata. That metadata can then be used to decide whether the value is admissible for a given study, product feature, or model training run.

## Tiers

- **Tier 1**: Highest confidence data, usually calibrated and directly verified.
- **Tier 2**: Moderately reliable data, often derived or partially validated.
- **Tier 3**: Lowest confidence data, such as self-reported or weakly validated input.

## Policy

A reliability policy defines the minimum score and maximum allowed tier. Data that fails the policy should be excluded automatically.
