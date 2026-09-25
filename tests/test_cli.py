import json

from data_reliability.cli import main


def test_cli_scans_jsonl_records(tmp_path, capsys):
    input_path = tmp_path / "records.jsonl"
    input_path.write_text('{"id":"a","value":1}\n{"id":"b","value":2}\n', encoding="utf-8")

    exit_code = main(
        [
            "scan",
            str(input_path),
            "--jsonl",
            "--source-id-field",
            "id",
            "--minimum-score",
            "70",
            "--maximum-tier",
            "2",
            "--evidence",
            '{"cryptographic_verification": 1.0}',
        ]
    )

    output = [json.loads(line) for line in capsys.readouterr().out.splitlines()]

    assert exit_code == 0
    assert [row["reliability"]["source_id"] for row in output] == ["a", "b"]
    assert all(row["decision"]["accepted"] for row in output)


def test_cli_reference_gate_evaluates_each_record(tmp_path, capsys):
    records = tmp_path / "records.jsonl"
    records.write_text('{"temperature":21.5}\n{"temperature":99}\n{}\n{"temperature":"invalid"}\n{"temperature":21.5}\n', encoding="utf-8")
    references = tmp_path / "references.json"
    references.write_text('[{"field":"temperature","value":21.5,"tolerance":0.2}]', encoding="utf-8")
    exit_code = main([
        "scan", str(records), "--jsonl", "--references", str(references),
        "--require-reference-checks", "--fail-on-rejection",
        "--minimum-score", "0", "--maximum-tier", "3", "--allow-unverified-timestamp",
    ])
    output = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert exit_code == 1
    assert [row["decision"]["accepted"] for row in output] == [True, False, False, False, True]
    assert output[1]["reliability"]["evidence_snapshot"]["reference_comparisons"][0]["observed"] == 99


def test_cli_without_evidence_rejects_by_default(tmp_path, capsys):
    records = tmp_path / "record.json"
    records.write_text('{"temperature":21.5}', encoding="utf-8")
    assert main(["scan", str(records), "--fail-on-rejection"]) == 1
    output = json.loads(capsys.readouterr().out)
    assert output["reliability"]["score"] == 0
    assert output["decision"]["accepted"] is False
