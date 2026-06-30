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
    "dri_timestamp_verified",
    "dri_calibration_version",
)


def metadata_to_columns(metadata: ReliabilityMetadata, *, prefix: str = "dri_") -> dict[str, Any]:
    """Return flat columns suitable for SQL tables and analytical databases."""
    return {
        f"{prefix}score": metadata.score,
        f"{prefix}tier": int(metadata.tier),
        f"{prefix}source_id": metadata.source_id,
        f"{prefix}trace_hash": metadata.trace_hash,
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


def trusted_records(records: Iterable[ReliableData], policy: ReliabilityPolicy) -> list[ReliableData]:
    """Filter an iterable of reliable records with one policy."""
    return [record for record in records if policy.allows(record.reliability)]
