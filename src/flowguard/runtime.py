from __future__ import annotations

import json
import time
from contextlib import contextmanager
from contextvars import ContextVar
from functools import wraps
from pathlib import Path
from typing import Any, Callable

from .artifacts import begin_run, write_run_artifacts
from .expectations import evaluate_expectations


_ACTIVE_WORKFLOW: ContextVar[str | None] = ContextVar("flowguard_active_workflow", default=None)


@contextmanager
def flowguard_run(workflow_name: str):
    begin_run(workflow_name)
    token = _ACTIVE_WORKFLOW.set(workflow_name)
    try:
        yield
    finally:
        _ACTIVE_WORKFLOW.reset(token)


def step(name: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            started = time.time()
            status = "success"
            output: Any = None
            error: str | None = None
            failures: list[str] = []
            try:
                output = func(*args, **kwargs)
                expectations = list(getattr(wrapper, "__flowguard_expectations__", []))
                failures = evaluate_expectations(output, expectations)
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
                        "source": _source_path(func),
                        "input_summary": _summarize({"args": args, "kwargs": kwargs}),
                        "output_summary": _summarize(output),
                        "failures": failures,
                        "error": error,
                    },
                    workflow=_ACTIVE_WORKFLOW.get() or "default",
                )

        setattr(wrapper, "__flowguard_expectations__", list(getattr(func, "__flowguard_expectations__", [])))
        setattr(wrapper, "__flowguard_step__", name)
        return wrapper

    return decorator


def _source_path(func: Callable[..., Any]) -> str:
    source = Path(func.__code__.co_filename)
    try:
        return str(source.resolve().relative_to(Path.cwd().resolve()))
    except ValueError:
        return str(source)


def _summarize(value: Any) -> str:
    try:
        text = json.dumps(value, ensure_ascii=False, default=str)
    except TypeError:
        text = repr(value)
    return text[:1000]
