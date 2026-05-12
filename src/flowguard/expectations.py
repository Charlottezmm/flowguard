from __future__ import annotations

import json
from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable


@dataclass(frozen=True)
class Expectation:
    kind: str
    params: dict[str, Any]


def _attach_expectation(func: Callable[..., Any], expectation: Expectation) -> Callable[..., Any]:
    current = list(getattr(func, "__flowguard_expectations__", []))
    current.append(expectation)
    setattr(func, "__flowguard_expectations__", current)
    return func


class expect:
    @staticmethod
    def valid_json() -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            return _attach_expectation(func, Expectation("valid_json", {}))

        return decorator

    @staticmethod
    def required_fields(path: str | list[str], fields: list[str] | None = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            params = {"path": path, "fields": fields}
            return _attach_expectation(func, Expectation("required_fields", params))

        return decorator

    @staticmethod
    def min_count(path: str, count: int) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            return _attach_expectation(func, Expectation("min_count", {"path": path, "count": count}))

        return decorator


def evaluate_expectations(output: Any, expectations: list[Expectation]) -> list[str]:
    failures: list[str] = []
    for item in expectations:
        if item.kind == "valid_json":
            if isinstance(output, str):
                try:
                    json.loads(output)
                except json.JSONDecodeError:
                    failures.append("output must be valid JSON")
            elif not isinstance(output, (dict, list)):
                failures.append("output must be JSON-like data")
        elif item.kind == "min_count":
            value = _get_path(output, item.params["path"])
            if not hasattr(value, "__len__") or len(value) < item.params["count"]:
                failures.append(f"{item.params['path']} must contain at least {item.params['count']} items")
        elif item.kind == "required_fields":
            failures.extend(_check_required_fields(output, item.params["path"], item.params["fields"]))
    return failures


def _get_path(value: Any, path: str) -> Any:
    current = value
    for part in path.split("."):
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current


def _check_required_fields(output: Any, path: str | list[str], fields: list[str] | None) -> list[str]:
    if isinstance(path, list):
        missing = [field for field in path if isinstance(output, dict) and field not in output]
        return [f"missing required field: {field}" for field in missing]

    if fields is None:
        return []

    if path.endswith(".*"):
        items = _get_path(output, path[:-2])
        if not isinstance(items, list):
            return [f"{path[:-2]} must be a list"]
        failures = []
        for index, item in enumerate(items):
            for field in fields:
                if not isinstance(item, dict) or field not in item:
                    failures.append(f"{path[:-2]}[{index}] missing {field}")
        return failures

    target = _get_path(output, path)
    if not isinstance(target, dict):
        return [f"{path} must be an object"]
    return [f"{path} missing {field}" for field in fields if field not in target]
