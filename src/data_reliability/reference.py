from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Optional, Sequence

from pydantic import BaseModel, Field

from .scanner import ValidationEvidence


class ReferenceComparison(BaseModel):
    """Comparison of an observed value against a predefined reference value."""

    reference_id: Optional[str] = None
    field: Optional[str] = None
    source: Optional[str] = None
    method: Optional[str] = None
    unit: Optional[str] = None
    observed: float
    reference: float
    tolerance: float = Field(gt=0.0)
    absolute_error: float = Field(ge=0.0)
    relative_error: Optional[float] = Field(default=None, ge=0.0)
    quality_score: float = Field(ge=0.0, le=1.0)
    passed: bool
    notes: list[str] = Field(default_factory=list)


class ReferenceValue(BaseModel):
    """Predefined reference or ground-truth value used for quality checks."""

    field: str
    value: float
    tolerance: float = Field(gt=0.0)
    reference_id: Optional[str] = None
    source: Optional[str] = None
    method: Optional[str] = None
    unit: Optional[str] = None


class ReferenceComparisonSet(BaseModel):
    """Aggregated result for all reference checks applied to a record."""

    comparisons: list[ReferenceComparison]
    passed: bool
    quality_score: float = Field(ge=0.0, le=1.0)
    notes: list[str] = Field(default_factory=list)


def compare_to_reference(
    value: Any,
    reference: float,
    *,
    tolerance: float,
    field: Optional[str] = None,
    reference_id: Optional[str] = None,
    source: Optional[str] = None,
    method: Optional[str] = None,
    unit: Optional[str] = None,
) -> ReferenceComparison:
    """Compare a measured value with a predefined reference or ground-truth value.

    The comparison is a value-quality signal. It is separate from trace hashes
    and HMAC signatures, which only verify payload integrity.
    """

    tolerance_value = float(tolerance)
    if tolerance_value <= 0.0:
        raise ValueError("tolerance must be greater than 0.0")

    observed = float(_extract_observed(value, field))
    reference_value = float(reference)
    absolute_error = abs(observed - reference_value)
    error_ratio = absolute_error / tolerance_value
    relative_error = None if reference_value == 0.0 else absolute_error / abs(reference_value)
    quality_score = round(1.0 / (1.0 + error_ratio), 4)
    passed = absolute_error <= tolerance_value

    target = f" for {field}" if field else ""
    status = "passed" if passed else "failed"
    context = []
    if reference_id:
        context.append(f"reference_id={reference_id}")
    if source:
        context.append(f"source={source}")
    if method:
        context.append(f"method={method}")
    context_text = f" ({', '.join(context)})" if context else ""
    notes = [
        f"Reference comparison {status}{target}{context_text}: "
        f"observed={observed}, reference={reference_value}, tolerance={tolerance_value}."
    ]

    return ReferenceComparison(
        reference_id=reference_id,
        field=field,
        source=source,
        method=method,
        unit=unit,
        observed=observed,
        reference=reference_value,
        tolerance=tolerance_value,
        absolute_error=absolute_error,
        relative_error=relative_error,
        quality_score=quality_score,
        passed=passed,
        notes=notes,
    )


def compare_to_references(value: Mapping[str, Any], references: Sequence[ReferenceValue]) -> ReferenceComparisonSet:
    """Compare one record with multiple predefined reference values."""

    comparisons = [
        compare_to_reference(
            value,
            reference=reference.value,
            tolerance=reference.tolerance,
            field=reference.field,
            reference_id=reference.reference_id,
            source=reference.source,
            method=reference.method,
            unit=reference.unit,
        )
        for reference in references
    ]
    if not comparisons:
        raise ValueError("at least one reference value is required")

    quality_score = round(sum(comparison.quality_score for comparison in comparisons) / len(comparisons), 4)
    passed = all(comparison.passed for comparison in comparisons)
    failed_fields = [comparison.field or "<value>" for comparison in comparisons if not comparison.passed]
    notes = [note for comparison in comparisons for note in comparison.notes]
    if failed_fields:
        notes.append(f"Reference set failed for fields: {', '.join(failed_fields)}.")
    else:
        notes.append("Reference set passed.")

    return ReferenceComparisonSet(
        comparisons=comparisons,
        passed=passed,
        quality_score=quality_score,
        notes=notes,
    )


def evidence_from_reference_comparison(
    comparison: ReferenceComparison | ReferenceComparisonSet,
    *,
    base: Optional[ValidationEvidence] = None,
    provenance: float = 1.0,
    schema_compliance: float = 1.0,
    calibration: float = 0.0,
    metadata_quality: float = 1.0,
) -> ValidationEvidence:
    """Turn a reference comparison into scanner evidence.

    Reference agreement updates consistency and anomaly evidence. A single
    failed reference check caps both fields at the failed comparison score.
    Provenance, calibration, schema compliance, and metadata quality remain
    explicit inputs because they come from the surrounding scientific workflow.
    """

    quality_score = comparison.quality_score
    evidence = base or ValidationEvidence(
        provenance=provenance,
        schema_compliance=schema_compliance,
        calibration=calibration,
        metadata_quality=metadata_quality,
    )
    return evidence.model_copy(
        update={
            "consistency": min(evidence.consistency, quality_score),
            "anomaly_detection": min(evidence.anomaly_detection, quality_score),
            "notes": [*evidence.notes, *comparison.notes],
        }
    )


def _extract_observed(value: Any, field: Optional[str]) -> Any:
    if field is None:
        return value
    if not isinstance(value, Mapping):
        raise TypeError("field can only be used when value is a mapping")
    if field not in value:
        raise KeyError(f"field is missing from value: {field}")
    return value[field]
