from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable


@dataclass(frozen=True)
class Expectation:
    kind: str
    params: dict[str, Any]


@dataclass(frozen=True)
class CheckResult:
    kind: str
    status: str
    message: str
    path: str | None = None
    params: dict[str, Any] = field(default_factory=dict)
    expected: Any = None
    actual: Any = None

    @property
    def passed(self) -> bool:
        return self.status == "passed"

    def to_dict(self) -> dict[str, Any]:
        result = {
            "kind": self.kind,
            "status": self.status,
            "message": self.message,
            "path": self.path,
            "params": self.params,
        }
        if self.expected is not None:
            result["expected"] = self.expected
        if self.actual is not None:
            result["actual"] = self.actual
        return result


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

    @staticmethod
    def non_empty(path: str | None = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            return _attach_expectation(func, Expectation("non_empty", {"path": path}))

        return decorator

    @staticmethod
    def max_length(path: str | None, length: int) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            return _attach_expectation(func, Expectation("max_length", {"path": path, "length": length}))

        return decorator

    @staticmethod
    def file_exists(path: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            return _attach_expectation(func, Expectation("file_exists", {"path": path}))

        return decorator

    @staticmethod
    def file_non_empty(path: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            return _attach_expectation(func, Expectation("file_non_empty", {"path": path}))

        return decorator

    @staticmethod
    def file_extension(path: str, extensions: list[str]) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            return _attach_expectation(func, Expectation("file_extension", {"path": path, "extensions": extensions}))

        return decorator

    @staticmethod
    def file_valid_json(path: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            return _attach_expectation(func, Expectation("file_valid_json", {"path": path}))

        return decorator

    @staticmethod
    def response_status(path: str | None = None, min: int = 200, max: int = 299) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            return _attach_expectation(func, Expectation("response_status", {"path": path, "min": min, "max": max}))

        return decorator

    @staticmethod
    def response_required_fields(path: str, fields: list[str]) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            return _attach_expectation(func, Expectation("response_required_fields", {"path": path, "fields": fields}))

        return decorator

    @staticmethod
    def response_non_empty(path: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            return _attach_expectation(func, Expectation("response_non_empty", {"path": path}))

        return decorator

    @staticmethod
    def no_error_envelope(path: str | None = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            return _attach_expectation(func, Expectation("no_error_envelope", {"path": path}))

        return decorator


def evaluate_expectations(output: Any, expectations: list[Expectation], base_dir: Path | str | None = None) -> list[str]:
    return [check.message for check in evaluate_checks(output, expectations, base_dir=base_dir) if check.status == "failed"]


def evaluate_expectation_results(output: Any, expectations: list[Expectation], base_dir: Path | str | None = None) -> list[CheckResult]:
    return evaluate_checks(output, expectations, base_dir=base_dir)


def evaluate_checks(output: Any, expectations: list[Expectation], base_dir: Path | str | None = None) -> list[CheckResult]:
    checks: list[CheckResult] = []
    resolved_base_dir = Path(base_dir) if base_dir is not None else Path.cwd()
    for item in expectations:
        if item.kind == "valid_json":
            checks.append(_check_valid_json(output, item))
        elif item.kind == "min_count":
            checks.append(_check_min_count(output, item))
        elif item.kind == "required_fields":
            checks.extend(_check_required_fields(output, item.params["path"], item.params["fields"]))
        elif item.kind == "non_empty":
            checks.append(_check_non_empty(output, item))
        elif item.kind == "max_length":
            checks.append(_check_max_length(output, item))
        elif item.kind == "file_exists":
            checks.append(_check_file_exists(output, item, resolved_base_dir))
        elif item.kind == "file_non_empty":
            checks.append(_check_file_non_empty(output, item, resolved_base_dir))
        elif item.kind == "file_extension":
            checks.append(_check_file_extension(output, item, resolved_base_dir))
        elif item.kind == "file_valid_json":
            checks.append(_check_file_valid_json(output, item, resolved_base_dir))
        elif item.kind == "response_status":
            checks.append(_check_response_status(output, item))
        elif item.kind == "response_required_fields":
            checks.extend(_check_required_fields(output, item.params["path"], item.params["fields"], kind=item.kind))
        elif item.kind == "response_non_empty":
            checks.append(_check_response_non_empty(output, item))
        elif item.kind == "no_error_envelope":
            checks.append(_check_no_error_envelope(output, item))
    return checks


def _check_valid_json(output: Any, item: Expectation) -> CheckResult:
    if isinstance(output, str):
        try:
            json.loads(output)
        except json.JSONDecodeError:
            return _failed(item.kind, None, "output must be valid JSON", item.params, expected="valid JSON", actual=output)
        return _passed(item.kind, None, "output is valid JSON", item.params)
    if not isinstance(output, (dict, list)):
        return _failed(item.kind, None, "output must be JSON-like data", item.params, expected="JSON-like data", actual=type(output).__name__)
    return _passed(item.kind, None, "output is JSON-like data", item.params)


def _check_min_count(output: Any, item: Expectation) -> CheckResult:
    path = item.params["path"]
    count = item.params["count"]
    value = _get_path(output, path)
    actual = len(value) if hasattr(value, "__len__") else None
    if actual is None or actual < count:
        return _failed(item.kind, path, f"{path} must contain at least {count} items", {"count": count}, expected=count, actual=actual)
    return _passed(item.kind, path, f"{path} contains at least {count} items", {"count": count}, expected=count, actual=actual)


def _check_non_empty(output: Any, item: Expectation) -> CheckResult:
    path = item.params["path"]
    value = _resolve_output(output, path)
    label = path or "output"
    if not _has_content(value):
        return _failed(item.kind, path, f"{label} must not be empty", {}, expected="non-empty", actual=value)
    return _passed(item.kind, path, f"{label} is not empty", {}, expected="non-empty", actual=value)


def _check_max_length(output: Any, item: Expectation) -> CheckResult:
    path = item.params["path"]
    length = item.params["length"]
    value = _resolve_output(output, path)
    actual = len(value) if hasattr(value, "__len__") else None
    label = path or "output"
    if actual is None or actual > length:
        return _failed(item.kind, path, f"{label} must contain at most {length} items", {"length": length}, expected=length, actual=actual)
    return _passed(item.kind, path, f"{label} contains at most {length} items", {"length": length}, expected=length, actual=actual)


def _check_file_exists(output: Any, item: Expectation, base_dir: Path) -> CheckResult:
    path = item.params["path"]
    resolved = _resolve_file_path(output, path, base_dir)
    if resolved is None or not resolved.exists():
        return _failed(item.kind, path, f"{path} must reference an existing file", {}, expected="existing file", actual=str(resolved) if resolved else None)
    return _passed(item.kind, path, f"{path} references an existing file", {}, expected="existing file", actual=str(resolved))


def _check_file_non_empty(output: Any, item: Expectation, base_dir: Path) -> CheckResult:
    path = item.params["path"]
    resolved = _resolve_file_path(output, path, base_dir)
    if resolved is None or not resolved.exists() or resolved.stat().st_size == 0:
        return _failed(item.kind, path, f"{path} must reference a non-empty file", {}, expected="non-empty file", actual=str(resolved) if resolved else None)
    return _passed(item.kind, path, f"{path} references a non-empty file", {}, expected="non-empty file", actual=str(resolved))


def _check_file_extension(output: Any, item: Expectation, base_dir: Path) -> CheckResult:
    path = item.params["path"]
    extensions = item.params["extensions"]
    resolved = _resolve_file_path(output, path, base_dir)
    actual = resolved.suffix if resolved else None
    if resolved is None or actual not in extensions:
        return _failed(item.kind, path, f"{path} must reference a file with an allowed extension", {"extensions": extensions}, expected=extensions, actual=actual)
    return _passed(item.kind, path, f"{path} references a file with an allowed extension", {"extensions": extensions}, expected=extensions, actual=actual)


def _check_file_valid_json(output: Any, item: Expectation, base_dir: Path) -> CheckResult:
    path = item.params["path"]
    resolved = _resolve_file_path(output, path, base_dir)
    if resolved is None or not resolved.exists():
        return _failed(item.kind, path, f"{path} must reference an existing JSON file", {}, expected="valid JSON file", actual=str(resolved) if resolved else None)
    try:
        json.loads(resolved.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _failed(item.kind, path, f"{path} must reference a valid JSON file", {}, expected="valid JSON file", actual=str(resolved))
    return _passed(item.kind, path, f"{path} references a valid JSON file", {}, expected="valid JSON file", actual=str(resolved))


def _check_response_status(output: Any, item: Expectation) -> CheckResult:
    path = item.params["path"]
    response = _resolve_output(output, path)
    status = _get_response_status(response)
    minimum = item.params["min"]
    maximum = item.params["max"]
    label = path or "response"
    if status is None or status < minimum or status > maximum:
        return _failed(item.kind, path, f"{label} status must be between {minimum} and {maximum}", {"min": minimum, "max": maximum}, expected=f"{minimum}-{maximum}", actual=status)
    return _passed(item.kind, path, f"{label} status is between {minimum} and {maximum}", {"min": minimum, "max": maximum}, expected=f"{minimum}-{maximum}", actual=status)


def _check_response_non_empty(output: Any, item: Expectation) -> CheckResult:
    path = item.params["path"]
    value = _get_path(output, path)
    if not _has_content(value):
        return _failed(item.kind, path, f"{path} must not be empty", {}, expected="non-empty", actual=value)
    return _passed(item.kind, path, f"{path} is not empty", {}, expected="non-empty", actual=value)


def _check_no_error_envelope(output: Any, item: Expectation) -> CheckResult:
    path = item.params["path"]
    value = _resolve_output(output, path)
    label = path or "response"
    if isinstance(value, dict) and any(key in value for key in ("error", "errors")):
        return _failed(item.kind, path, f"{label} must not contain an error envelope", {}, expected="no error envelope", actual=value)
    return _passed(item.kind, path, f"{label} does not contain an error envelope", {}, expected="no error envelope", actual=value)


def _resolve_output(output: Any, path: str | None) -> Any:
    if path is None:
        return output
    return _get_path(output, path)


def _has_content(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if hasattr(value, "__len__"):
        return len(value) > 0
    return True


def _get_path(value: Any, path: str) -> Any:
    current = value
    for part in path.split("."):
        if isinstance(current, dict):
            current = current.get(part)
        else:
            current = getattr(current, part, None)
    return current


def _resolve_file_path(output: Any, path: str, base_dir: Path) -> Path | None:
    value = _get_path(output, path)
    if not isinstance(value, str):
        return None
    candidate = Path(value)
    if candidate.is_absolute():
        return candidate
    return base_dir / candidate


def _get_response_status(response: Any) -> int | None:
    if isinstance(response, dict):
        value = response.get("status_code", response.get("status"))
    else:
        value = getattr(response, "status_code", getattr(response, "status", None))
    return value if isinstance(value, int) else None


def _check_required_fields(
    output: Any,
    path: str | list[str],
    fields: list[str] | None,
    kind: str = "required_fields",
) -> list[CheckResult]:
    if isinstance(path, list):
        if not isinstance(output, dict):
            return [_failed(kind, None, "output must be an object", {"fields": path}, expected="object", actual=type(output).__name__)]
        missing = [field for field in path if field not in output]
        if missing:
            return [_failed(kind, field, f"missing required field: {field}", {"fields": path}, expected="present", actual="missing") for field in missing]
        return [_passed(kind, None, "all required fields are present", {"fields": path})]

    if fields is None:
        return []

    if path.endswith(".*"):
        items = _get_path(output, path[:-2])
        if not isinstance(items, list):
            return [_failed(kind, path[:-2], f"{path[:-2]} must be a list", {"fields": fields}, expected="list", actual=type(items).__name__)]
        results = []
        for index, item in enumerate(items):
            for field_name in fields:
                if not isinstance(item, dict) or field_name not in item:
                    results.append(
                        _failed(
                            kind,
                            f"{path[:-2]}[{index}].{field_name}",
                            f"{path[:-2]}[{index}] missing {field_name}",
                            {"fields": fields},
                            expected="present",
                            actual="missing",
                        )
                    )
        return results or [_passed(kind, path, "all required item fields are present", {"fields": fields})]

    target = _get_path(output, path)
    if not isinstance(target, dict):
        return [_failed(kind, path, f"{path} must be an object", {"fields": fields}, expected="object", actual=type(target).__name__)]
    missing = [field_name for field_name in fields if field_name not in target]
    if missing:
        return [_failed(kind, f"{path}.{field_name}", f"{path} missing {field_name}", {"fields": fields}, expected="present", actual="missing") for field_name in missing]
    return [_passed(kind, path, "all required fields are present", {"fields": fields})]


def _passed(
    kind: str,
    path: str | None,
    message: str,
    params: dict[str, Any],
    expected: Any = None,
    actual: Any = None,
) -> CheckResult:
    return CheckResult(kind=kind, status="passed", message=message, path=path, params=params, expected=expected, actual=actual)


def _failed(
    kind: str,
    path: str | None,
    message: str,
    params: dict[str, Any],
    expected: Any = None,
    actual: Any = None,
) -> CheckResult:
    return CheckResult(kind=kind, status="failed", message=message, path=path, params=params, expected=expected, actual=actual)
