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
