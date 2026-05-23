from __future__ import annotations

from flowguard.expectations import Expectation, evaluate_expectations


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
