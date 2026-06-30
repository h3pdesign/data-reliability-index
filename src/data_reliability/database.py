from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any, Optional

from .core import DataTier, ReliableData, ReliabilityMetadata, ReliabilityPolicy
from .scanner import ReliabilityScanner, ValidationEvidence

RELIABILITY_COLUMNS = (
    "dri_score",
    "dri_tier",
    "dri_source_id",
    "dri_trace_hash",
    "dri_profile_name",
    "dri_profile_version",
    "dri_timestamp_verified",
    "dri_calibration_version",
)

SQL_DIALECT_TYPES: dict[str, dict[str, str]] = {
    "sqlite": {
        "integer": "INTEGER",
        "text": "TEXT",
        "boolean": "INTEGER",
    },
    "postgres": {
        "integer": "INTEGER",
        "text": "TEXT",
        "boolean": "BOOLEAN",
    },
    "mysql": {
        "integer": "INT",
        "text": "VARCHAR(512)",
        "boolean": "BOOLEAN",
    },
    "duckdb": {
        "integer": "INTEGER",
        "text": "VARCHAR",
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
        f"{prefix}timestamp_verified": metadata.timestamp_verified,
        f"{prefix}calibration_version": metadata.calibration_version,
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
        timestamp_verified=bool(row.get(f"{prefix}timestamp_verified", True)),
        calibration_version=row.get(f"{prefix}calibration_version"),
    )


def metadata_to_document(metadata: ReliabilityMetadata) -> dict[str, Any]:
    """Return JSON-friendly metadata for document databases and object stores."""
    document = metadata.model_dump(mode="json")
    document["tier"] = int(metadata.tier)
    return document


def metadata_from_document(document: Mapping[str, Any]) -> ReliabilityMetadata:
    """Rebuild metadata from a JSON/document-store representation."""
    return ReliabilityMetadata.model_validate(document)


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
        f"{prefix}timestamp_verified": types["boolean"],
        f"{prefix}calibration_version": types["text"],
    }


def reliability_columns_ddl(*, prefix: str = "dri_", dialect: str = "sqlite") -> str:
    """Return a comma-separated SQL fragment for adding DRI columns to a table."""
    definitions = reliability_column_definitions(prefix=prefix, dialect=dialect)
    return ",\n".join(f"{name} {column_type}" for name, column_type in definitions.items())
