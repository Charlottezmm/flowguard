from __future__ import annotations

import argparse
from pathlib import Path

from .comparison import compare_runs
from .golden import compare_golden, create_golden
from .golden import normalize_run
from .query import list_named_runs, load_agent_context, load_latest_run, load_named_run, load_workflow_map, save_named_run, summarize_run


def main() -> None:
    parser = argparse.ArgumentParser(prog="flowguard")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("context")
    subparsers.add_parser("status")

    run_parser = subparsers.add_parser("run")
    run_subparsers = run_parser.add_subparsers(dest="run_command")
    run_subparsers.required = True
    run_save = run_subparsers.add_parser("save")
    run_save.add_argument("--workflow", required=True)
    run_save.add_argument("--name", required=True)
    run_list = run_subparsers.add_parser("list")
    run_list.add_argument("--workflow")
    run_compare = run_subparsers.add_parser("compare")
    run_compare.add_argument("--workflow", required=True)
    run_compare.add_argument("--left", required=True)
    run_compare.add_argument("--right", required=True)

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
    try:
        if args.command in {None, "context"}:
            _print_context()
        elif args.command == "status":
            print(summarize_run())
        elif args.command == "run" and args.run_command == "save":
            path = save_named_run(args.workflow, args.name)
            print(f"Saved named run: {path}")
        elif args.command == "run" and args.run_command == "list":
            runs = list_named_runs(args.workflow)
            for item in runs:
                print(f"{item['workflow']}/{item['name']}")
        elif args.command == "run" and args.run_command == "compare":
            left = _load_normalized_run_reference(args.workflow, args.left)
            right = _load_normalized_run_reference(args.workflow, args.right)
            result = compare_runs(left, right, left_label=args.left, right_label=args.right)
            if result.passed:
                print(f"Run comparison passed: {args.left} -> {args.right}")
            else:
                print(f"Run comparison failed: {args.left} -> {args.right}")
                print()
                print(result.agent_diff)
                raise SystemExit(1)
        elif args.command == "golden" and args.golden_command == "create":
            path = create_golden(args.workflow, args.name)
            print(f"Created golden baseline: {path}")
        elif args.command == "golden" and args.golden_command == "compare":
            result = compare_golden(args.workflow, args.name)
            if result.passed:
                print(f"Golden comparison passed: {result.baseline_path}")
            else:
                print(f"Golden comparison failed: {result.baseline_path}")
                print()
                print(result.agent_diff)
                raise SystemExit(1)
    except (FileNotFoundError, ValueError) as exc:
        parser.exit(1, f"FlowGuard error: {exc}\n")


def _print_context() -> None:
    latest = Path(".flowguard/runs/latest/agent_context.md")
    if latest.exists():
        print(load_agent_context())
    else:
        print("No FlowGuard run found.")


def _load_normalized_run_reference(workflow: str, reference: str) -> dict:
    if reference == "latest":
        trace = load_latest_run()
        if trace.get("workflow") != workflow:
            raise ValueError(f"latest workflow is {trace.get('workflow')}, not {workflow}")
        return normalize_run(trace, load_workflow_map())

    named_run = load_named_run(workflow, reference)
    return normalize_run(named_run["trace"], named_run["workflow_map"])


if __name__ == "__main__":
    main()
