from __future__ import annotations

import json
import time
from contextlib import contextmanager
from contextvars import ContextVar
from functools import wraps
from pathlib import Path
from typing import Any, Callable

from .artifacts import begin_run, write_run_artifacts
from .expectations import evaluate_checks


_ACTIVE_WORKFLOW: ContextVar[str | None] = ContextVar("flowguard_active_workflow", default=None)
_ACTIVE_RUN_ROOT: ContextVar[Path | None] = ContextVar("flowguard_active_run_root", default=None)


@contextmanager
def flowguard_run(workflow_name: str):
    run_root = Path.cwd().resolve()
    begin_run(workflow_name, run_root=run_root)
    workflow_token = _ACTIVE_WORKFLOW.set(workflow_name)
    root_token = _ACTIVE_RUN_ROOT.set(run_root)
    try:
        yield
    finally:
        _ACTIVE_RUN_ROOT.reset(root_token)
        _ACTIVE_WORKFLOW.reset(workflow_token)


def step(name: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            started = time.time()
            run_root = _ACTIVE_RUN_ROOT.get() or Path.cwd().resolve()
            status = "success"
            output: Any = None
            error: str | None = None
            failures: list[str] = []
            checks: list[dict[str, Any]] = []
            try:
                output = func(*args, **kwargs)
                expectations = list(getattr(wrapper, "__flowguard_expectations__", []))
                results = evaluate_checks(output, expectations, base_dir=run_root)
                checks = [result.to_dict() for result in results]
                failures = [result.message for result in results if result.status == "failed"]
                if failures:
                    status = "failed"
                return output
            except Exception as exc:
                status = "error"
                error = repr(exc)
                raise
            finally:
                duration_ms = round((time.time() - started) * 1000)
                write_run_artifacts(
                    {
                        "id": name,
                        "name": name,
                        "status": status,
                        "duration_ms": duration_ms,
                        "source": _source_path(func, run_root),
                        "input_summary": _summarize({"args": args, "kwargs": kwargs}),
                        "output_summary": _summarize(output),
                        "failures": failures,
                        "checks": checks,
                        "error": error,
                    },
                    workflow=_ACTIVE_WORKFLOW.get() or "default",
                    run_root=run_root,
                )

        setattr(wrapper, "__flowguard_expectations__", list(getattr(func, "__flowguard_expectations__", [])))
        setattr(wrapper, "__flowguard_step__", name)
        return wrapper

    return decorator


def _source_path(func: Callable[..., Any], base_dir: Path) -> str:
    source = Path(func.__code__.co_filename)
    try:
        return str(source.resolve().relative_to(base_dir))
    except ValueError:
        return str(source)


def _summarize(value: Any) -> str:
    try:
        text = json.dumps(value, ensure_ascii=False, default=str)
    except TypeError:
        text = repr(value)
    return text[:1000]
