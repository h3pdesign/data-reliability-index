from __future__ import annotations

import argparse
import json
import sys
from contextlib import nullcontext
from collections.abc import Iterable
from typing import Any, ContextManager, TextIO

from .core import DataTier, ReliabilityPolicy
from .database import decision_to_document, metadata_to_document
from .reference import ReferenceValue
from .scanner import ReliabilityProfile, ReliabilityScanner, ValidationEvidence, climate_record_profile, default_profile, scientific_profile


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="dri", description="Scan JSON records with Data Reliability Index.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan_parser = subparsers.add_parser("scan", help="Scan JSON or JSONL records.")
    scan_parser.add_argument("input", nargs="?", default="-", help="JSON/JSONL input file, or '-' for stdin.")
    scan_parser.add_argument("--jsonl", action="store_true", help="Read newline-delimited JSON records.")
    scan_parser.add_argument("--profile", choices=["default", "scientific", "climate-record"], default="default")
    scan_parser.add_argument("--source-id", default="cli", help="Source id for records without --source-id-field.")
    scan_parser.add_argument("--source-id-field", help="Use this field from each JSON object as the source id.")
    scan_parser.add_argument("--required-field", action="append", default=[], help="Required field; repeat for multiple fields.")
    scan_parser.add_argument("--minimum-score", type=int, default=70)
    scan_parser.add_argument("--maximum-tier", type=int, choices=[1, 2, 3], default=2)
    scan_parser.add_argument("--allow-unverified-timestamp", action="store_true")
    scan_parser.add_argument("--evidence", help="JSON object with ValidationEvidence fields.")
    scan_parser.add_argument("--references", help="JSON file containing a list of predefined ReferenceValue objects.")
    scan_parser.add_argument("--require-reference-checks", action="store_true")
    scan_parser.add_argument("--fail-on-rejection", action="store_true", help="Exit with status 1 if any record is rejected.")

    args = parser.parse_args(argv)
    if args.command == "scan":
        return _scan_command(args)
    return 2


def _scan_command(args: argparse.Namespace) -> int:
    scanner = ReliabilityScanner(profile=_profile(args.profile))
    policy = ReliabilityPolicy(
        minimum_score=args.minimum_score,
        maximum_tier=DataTier(args.maximum_tier),
        require_timestamp_verified=not args.allow_unverified_timestamp,
        require_reference_checks=args.require_reference_checks,
    )
    evidence = ValidationEvidence.model_validate(json.loads(args.evidence)) if args.evidence else None
    references = None
    if args.references:
        with open(args.references, encoding="utf-8") as handle:
            definitions = json.load(handle)
        if not isinstance(definitions, list) or not definitions:
            raise ValueError("--references must contain a non-empty JSON list")
        references = [ReferenceValue.model_validate(item) for item in definitions]
    rejected = False

    with _open_input(args.input) as handle:
        records = _read_jsonl(handle) if args.jsonl else _read_json(handle)
        for record in records:
            source_id = _source_id(record, args.source_id, args.source_id_field)
            reliable = scanner.scan(record, source_id=source_id, evidence=evidence, required_fields=args.required_field, references=references)
            decision = policy.assess(reliable.reliability)
            rejected = rejected or not decision.accepted
            output = {
                "value": reliable.value,
                "reliability": metadata_to_document(reliable.reliability),
                "decision": decision_to_document(decision),
            }
            print(json.dumps(output, sort_keys=True))
    return 1 if rejected and args.fail_on_rejection else 0


def _profile(name: str) -> ReliabilityProfile:
    if name == "scientific":
        return scientific_profile()
    if name == "climate-record":
        return climate_record_profile()
    return default_profile()


def _open_input(path: str) -> ContextManager[TextIO]:
    if path == "-":
        return nullcontext(sys.stdin)
    return open(path, encoding="utf-8")


def _read_json(handle: TextIO) -> Iterable[Any]:
    data = json.load(handle)
    if isinstance(data, list):
        return data
    return [data]


def _read_jsonl(handle: TextIO) -> Iterable[Any]:
    return (json.loads(line) for line in handle if line.strip())


def _source_id(record: Any, fallback: str, source_id_field: str | None) -> str:
    if source_id_field is None:
        return fallback
    if not isinstance(record, dict):
        raise ValueError("--source-id-field requires JSON object records")
    return str(record[source_id_field])


if __name__ == "__main__":
    raise SystemExit(main())
