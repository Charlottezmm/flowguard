from flowguard import expect, flowguard_run, step


@step("issue.parse")
@expect.required_fields(["title", "body"])
def parse_issue(raw_text: str) -> dict:
    return {
        "title": "FlowGuard report is empty after running the workflow",
        "body": raw_text,
    }


@step("issue.triage")
@expect.required_fields(["issue_type", "severity", "repro_steps", "affected_files"])
@expect.min_count("repro_steps", 2)
@expect.min_count("affected_files", 1)
def triage_issue(issue: dict) -> dict:
    # Intentionally incomplete so the demo produces agent repair context.
    return {
        "issue_type": "bug",
        "severity": "medium",
        "repro_steps": [
            "Run the GitHub issue triage demo.",
        ],
        "affected_files": [],
    }


@step("repair_brief.create")
@expect.required_fields(["summary", "suggested_focus"])
def create_repair_brief(triage: dict) -> dict:
    return {
        "summary": "The workflow completed, but the triage output is incomplete.",
        "suggested_focus": "Add enough repro steps and affected files before handing off to a coding agent.",
    }


def main() -> None:
    with flowguard_run("github_issue_triage"):
        issue = parse_issue(
            "After running the workflow, .flowguard/runs/latest/agent_context.md exists but does not explain the failure."
        )
        triage = triage_issue(issue)
        create_repair_brief(triage)


if __name__ == "__main__":
    main()
