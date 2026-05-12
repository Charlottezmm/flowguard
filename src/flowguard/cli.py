from __future__ import annotations

from pathlib import Path


def main() -> None:
    latest = Path(".flowguard/runs/latest/agent_context.md")
    if latest.exists():
        print(latest.read_text(encoding="utf-8"))
    else:
        print("No FlowGuard run found.")


if __name__ == "__main__":
    main()
