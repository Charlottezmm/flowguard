from __future__ import annotations

import argparse
from pathlib import Path

from .golden import compare_golden, create_golden
from .query import load_agent_context, summarize_run


def main() -> None:
    parser = argparse.ArgumentParser(prog="flowguard")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("context")
    subparsers.add_parser("status")

    golden_parser = subparsers.add_parser("golden")
    golden_subparsers = golden_parser.add_subparsers(dest="golden_command")
    golden_subparsers.required = True
    golden_create = golden_subparsers.add_parser("create")
    golden_create.add_argument("--workflow", required=True)
    golden_create.add_argument("--name", default="default")
    golden_compare = golden_subparsers.add_parser("compare")
    golden_compare.add_argument("--workflow", required=True)
    golden_compare.add_argument("--name", default="default")

    args = parser.parse_args()
    if args.command in {None, "context"}:
        _print_context()
    elif args.command == "status":
        print(summarize_run())
    elif args.command == "golden" and args.golden_command == "create":
        path = create_golden(args.workflow, args.name)
        print(f"Created golden baseline: {path}")
    elif args.command == "golden" and args.golden_command == "compare":
        result = compare_golden(args.workflow, args.name)
        if result.passed:
            print(f"Golden comparison passed: {result.baseline_path}")
        else:
            print(f"Golden comparison failed: {result.baseline_path}")
            for difference in result.differences:
                print(f"- {difference}")
            raise SystemExit(1)


def _print_context() -> None:
    latest = Path(".flowguard/runs/latest/agent_context.md")
    if latest.exists():
        print(load_agent_context())
    else:
        print("No FlowGuard run found.")


if __name__ == "__main__":
    main()
