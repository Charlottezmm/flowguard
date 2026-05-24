from __future__ import annotations

from pathlib import Path

from flowguard.expectations import Expectation, evaluate_checks, evaluate_expectations


def test_evaluate_required_fields_and_counts() -> None:
    output = {
        "title": "Bug",
        "items": [{"name": "first"}, {}],
    }

    failures = evaluate_expectations(
        output,
        [
            Expectation("required_fields", {"path": ["title", "body"], "fields": None}),
            Expectation("required_fields", {"path": "items.*", "fields": ["name"]}),
            Expectation("min_count", {"path": "items", "count": 3}),
        ],
    )

    assert failures == [
        "missing required field: body",
        "items[1] missing name",
        "items must contain at least 3 items",
    ]


def test_evaluate_valid_json_non_empty_and_max_length() -> None:
    failures = evaluate_expectations(
        {"summary": "", "tags": ["bug", "regression", "ui"]},
        [
            Expectation("valid_json", {}),
            Expectation("non_empty", {"path": "summary"}),
            Expectation("max_length", {"path": "tags", "length": 2}),
        ],
    )

    assert failures == [
        "summary must not be empty",
        "tags must contain at most 2 items",
    ]


def test_invalid_json_string_fails() -> None:
    failures = evaluate_expectations("not json", [Expectation("valid_json", {})])

    assert failures == ["output must be valid JSON"]


def test_structured_check_results_preserve_failure_messages() -> None:
    checks = evaluate_checks(
        {"items": [], "summary": ""},
        [
            Expectation("min_count", {"path": "items", "count": 2}),
            Expectation("non_empty", {"path": "summary"}),
        ],
    )

    assert [check.to_dict() for check in checks] == [
        {
            "kind": "min_count",
            "status": "failed",
            "message": "items must contain at least 2 items",
            "path": "items",
            "params": {"count": 2},
            "expected": 2,
            "actual": 0,
        },
        {
            "kind": "non_empty",
            "status": "failed",
            "message": "summary must not be empty",
            "path": "summary",
            "params": {},
            "expected": "non-empty",
            "actual": "",
        },
    ]

    assert [check.message for check in checks if check.status == "failed"] == evaluate_expectations(
        {"items": [], "summary": ""},
        [
            Expectation("min_count", {"path": "items", "count": 2}),
            Expectation("non_empty", {"path": "summary"}),
        ],
    )


def test_structured_checks_include_passed_results_without_failures() -> None:
    checks = evaluate_checks({"items": ["a", "b"]}, [Expectation("min_count", {"path": "items", "count": 2})])

    assert [check.to_dict() for check in checks] == [
        {
            "kind": "min_count",
            "status": "passed",
            "message": "items contains at least 2 items",
            "path": "items",
            "params": {"count": 2},
            "expected": 2,
            "actual": 2,
        }
    ]
    assert evaluate_expectations({"items": ["a", "b"]}, [Expectation("min_count", {"path": "items", "count": 2})]) == []


def test_file_artifact_checks(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    data_path = Path("artifacts/result.json")
    empty_path = Path("artifacts/empty.txt")
    data_path.parent.mkdir()
    data_path.write_text('{"ok": true}', encoding="utf-8")
    empty_path.write_text("", encoding="utf-8")

    output = {"result": {"path": str(data_path), "empty": str(empty_path), "missing": "artifacts/missing.json"}}

    checks = evaluate_checks(
        output,
        [
            Expectation("file_exists", {"path": "result.path"}),
            Expectation("file_non_empty", {"path": "result.empty"}),
            Expectation("file_extension", {"path": "result.path", "extensions": [".json"]}),
            Expectation("file_valid_json", {"path": "result.path"}),
            Expectation("file_exists", {"path": "result.missing"}),
        ],
    )

    assert [check.status for check in checks] == ["passed", "failed", "passed", "passed", "failed"]
    assert [check.message for check in checks if check.status == "failed"] == [
        "result.empty must reference a non-empty file",
        "result.missing must reference an existing file",
    ]


def test_api_like_response_checks_do_not_make_network_calls() -> None:
    output = {
        "response": {
            "status_code": 429,
            "json": {"items": [], "error": "rate limited"},
        }
    }

    failures = evaluate_expectations(
        output,
        [
            Expectation("response_status", {"path": "response", "min": 200, "max": 299}),
            Expectation("response_non_empty", {"path": "response.json.items"}),
            Expectation("no_error_envelope", {"path": "response.json"}),
        ],
    )

    assert failures == [
        "response status must be between 200 and 299",
        "response.json.items must not be empty",
        "response.json must not contain an error envelope",
    ]
