from __future__ import annotations

from pathlib import Path


def validate_path_segment(label: str, value: str) -> None:
    path = Path(value)
    if (
        not value
        or value in {".", ".."}
        or path.is_absolute()
        or path.name != value
        or "/" in value
        or "\\" in value
        or ".." in path.parts
    ):
        raise ValueError(f"{label} must be a simple path segment: {value!r}")
