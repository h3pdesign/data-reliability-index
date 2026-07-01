from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from typing import Any, Optional

from .core import DataTier, ReliableData, ReliabilityDecision, ReliabilityMetadata, ReliabilityPolicy
from .scanner import ReliabilityScanner, ValidationEvidence

RELIABILITY_COLUMNS = (
    "dri_score",
    "dri_tier",
    "dri_source_id",
    "dri_trace_hash",
    "dri_profile_name",
    "dri_profile_version",
    "dri_evidence_hash",
    "dri_evidence_snapshot",
    "dri_timestamp_verified",
    "dri_calibration_version",
    "dri_evidence_confidence",
    "dri_uncertainty",
)

SQL_DIALECT_TYPES: dict[str, dict[str, str]] = {
    "sqlite": {
        "integer": "INTEGER",
        "real": "REAL",
        "text": "TEXT",
        "longtext": "TEXT",
        "boolean": "INTEGER",
    },
    "postgres": {
        "integer": "INTEGER",
        "real": "DOUBLE PRECISION",
        "text": "TEXT",
        "longtext": "TEXT",
        "boolean": "BOOLEAN",
    },
    "mysql": {
        "integer": "INT",
        "real": "DOUBLE",
        "text": "VARCHAR(512)",
        "longtext": "TEXT",
        "boolean": "BOOLEAN",
    },
    "duckdb": {
        "integer": "INTEGER",
        "real": "DOUBLE",
        "text": "VARCHAR",
        "longtext": "VARCHAR",
        "boolean": "BOOLEAN",
    },
}


def metadata_to_columns(metadata: ReliabilityMetadata, *, prefix: str = "dri_") -> dict[str, Any]:
    """Return flat columns suitable for SQL tables and analytical databases."""
    return {
        f"{prefix}score": metadata.score,
        f"{prefix}tier": int(metadata.tier),
        f"{prefix}source_id": metadata.source_id,
        f"{prefix}trace_hash": metadata.trace_hash,
        f"{prefix}profile_name": metadata.profile_name,
        f"{prefix}profile_version": metadata.profile_version,
        f"{prefix}evidence_hash": metadata.evidence_hash,
        f"{prefix}evidence_snapshot": json.dumps(metadata.evidence_snapshot, sort_keys=True) if metadata.evidence_snapshot else None,
        f"{prefix}timestamp_verified": metadata.timestamp_verified,
        f"{prefix}calibration_version": metadata.calibration_version,
        f"{prefix}evidence_confidence": metadata.evidence_confidence,
        f"{prefix}uncertainty": metadata.uncertainty,
    }


def metadata_from_columns(row: Mapping[str, Any], *, prefix: str = "dri_") -> ReliabilityMetadata:
    """Rebuild reliability metadata from flat SQL-style columns."""
    return ReliabilityMetadata(
        score=int(row[f"{prefix}score"]),
        tier=DataTier(int(row[f"{prefix}tier"])),
        source_id=str(row[f"{prefix}source_id"]),
        trace_hash=str(row[f"{prefix}trace_hash"]),
        profile_name=str(row.get(f"{prefix}profile_name", "default")),
        profile_version=str(row.get(f"{prefix}profile_version", "1")),
        evidence_hash=_optional_str(row.get(f"{prefix}evidence_hash")),
        evidence_snapshot=_coerce_json_object(row.get(f"{prefix}evidence_snapshot")),
        timestamp_verified=_coerce_bool(row.get(f"{prefix}timestamp_verified", True)),
        calibration_version=row.get(f"{prefix}calibration_version"),
        evidence_confidence=float(row.get(f"{prefix}evidence_confidence", 1.0)),
        uncertainty=_optional_float(row.get(f"{prefix}uncertainty")),
    )


def _coerce_bool(value: Any) -> bool:
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"0", "false", "f", "no", "n", "off"}:
            return False
        if normalized in {"1", "true", "t", "yes", "y", "on"}:
            return True
    return bool(value)


def _optional_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    return str(value)


def _optional_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    return float(value)


def _coerce_json_object(value: Any) -> Optional[dict[str, Any]]:
    if value is None:
        return None
    if isinstance(value, Mapping):
        return dict(value)
    if isinstance(value, str):
        return dict(json.loads(value))
    raise TypeError("Evidence snapshot must be a mapping, JSON object string, or None.")


def metadata_to_document(metadata: ReliabilityMetadata) -> dict[str, Any]:
    """Return JSON-friendly metadata for document databases and object stores."""
    document = metadata.model_dump(mode="json")
    document["tier"] = int(metadata.tier)
    return document


def metadata_from_document(document: Mapping[str, Any]) -> ReliabilityMetadata:
    """Rebuild metadata from a JSON/document-store representation."""
    return ReliabilityMetadata.model_validate(document)


def decision_to_columns(decision: ReliabilityDecision, *, prefix: str = "dri_decision_") -> dict[str, Any]:
    """Return flat accept/reject decision columns for audit logs."""
    return {
        f"{prefix}accepted": decision.accepted,
        f"{prefix}score_passed": decision.score_passed,
        f"{prefix}tier_passed": decision.tier_passed,
        f"{prefix}timestamp_passed": decision.timestamp_passed,
        f"{prefix}minimum_score": decision.policy.minimum_score,
        f"{prefix}maximum_tier": int(decision.policy.maximum_tier),
        f"{prefix}require_timestamp_verified": decision.policy.require_timestamp_verified,
        f"{prefix}reasons": "; ".join(decision.reasons),
    }


def decision_to_document(decision: ReliabilityDecision) -> dict[str, Any]:
    """Return a JSON-friendly accept/reject decision for document stores and logs."""
    document = decision.model_dump(mode="json")
    document["policy"]["maximum_tier"] = int(decision.policy.maximum_tier)
    document["metadata"] = metadata_to_document(decision.metadata)
    return document


def scan_row(
    row: Mapping[str, Any],
    *,
    source_id: str,
    evidence: Optional[ValidationEvidence] = None,
    scanner: Optional[ReliabilityScanner] = None,
    required_fields: Optional[Iterable[str]] = None,
) -> dict[str, Any]:
    """Attach DRI columns to one database row without mutating the input row."""
    active_scanner = scanner or ReliabilityScanner()
    reliable = active_scanner.scan(
        dict(row),
        source_id=source_id,
        evidence=evidence,
        required_fields=list(required_fields) if required_fields is not None else None,
    )
    return {**dict(row), **metadata_to_columns(reliable.reliability)}


def scan_rows(
    rows: Iterable[Mapping[str, Any]],
    *,
    source_id_field: Optional[str] = None,
    source_id: str = "dataset",
    evidence: Optional[ValidationEvidence] = None,
    scanner: Optional[ReliabilityScanner] = None,
    required_fields: Optional[Iterable[str]] = None,
) -> list[dict[str, Any]]:
    """Scan rows into a list with reliability columns attached."""
    return list(
        iter_scan_rows(
            rows,
            source_id_field=source_id_field,
            source_id=source_id,
            evidence=evidence,
            scanner=scanner,
            required_fields=required_fields,
        )
    )


def iter_scan_rows(
    rows: Iterable[Mapping[str, Any]],
    *,
    source_id_field: Optional[str] = None,
    source_id: str = "dataset",
    evidence: Optional[ValidationEvidence] = None,
    scanner: Optional[ReliabilityScanner] = None,
    required_fields: Optional[Iterable[str]] = None,
) -> Iterable[dict[str, Any]]:
    """Yield scanned rows one at a time for large datasets."""
    active_scanner = scanner or ReliabilityScanner()
    required = list(required_fields) if required_fields is not None else None
    for row in rows:
        row_source_id = str(row[source_id_field]) if source_id_field is not None else source_id
        yield scan_row(
            row,
            source_id=row_source_id,
            evidence=evidence,
            scanner=active_scanner,
            required_fields=required,
        )


def trusted_records(records: Iterable[ReliableData], policy: ReliabilityPolicy) -> list[ReliableData]:
    """Filter an iterable of reliable records with one policy."""
    return [record for record in records if policy.allows(record.reliability)]


def reliability_column_definitions(*, prefix: str = "dri_", dialect: str = "sqlite") -> dict[str, str]:
    """Return SQL column definitions for the supported reliability columns."""
    types = SQL_DIALECT_TYPES.get(dialect.lower())
    if types is None:
        supported = ", ".join(sorted(SQL_DIALECT_TYPES))
        raise ValueError(f"Unsupported SQL dialect: {dialect}. Supported dialects: {supported}")
    return {
        f"{prefix}score": types["integer"],
        f"{prefix}tier": types["integer"],
        f"{prefix}source_id": types["text"],
        f"{prefix}trace_hash": types["text"],
        f"{prefix}profile_name": types["text"],
        f"{prefix}profile_version": types["text"],
        f"{prefix}evidence_hash": types["text"],
        f"{prefix}evidence_snapshot": types["longtext"],
        f"{prefix}timestamp_verified": types["boolean"],
        f"{prefix}calibration_version": types["text"],
        f"{prefix}evidence_confidence": types["real"],
        f"{prefix}uncertainty": types["real"],
    }


def reliability_columns_ddl(*, prefix: str = "dri_", dialect: str = "sqlite") -> str:
    """Return a comma-separated SQL fragment for adding DRI columns to a table."""
    definitions = reliability_column_definitions(prefix=prefix, dialect=dialect)
    return ",\n".join(f"{name} {column_type}" for name, column_type in definitions.items())
