from __future__ import annotations

import argparse

from flowguard import expect, flowguard_run, step


WORKFLOW = "support_reply_case_study"


@step("support.ticket.parse")
@expect.required_fields(["customer_id", "problem", "observed_signals"])
def parse_ticket() -> dict:
    return {
        "customer_id": "acme-42",
        "problem": "Export finished successfully but the CSV is missing invoice rows.",
        "observed_signals": [
            "The export job returned status=success.",
            "The row count dropped from 120 to 84.",
            "Invoice rows are absent from the exported CSV.",
        ],
    }


@step("support.reply")
@expect.required_fields(["answer", "evidence_items", "next_action"])
@expect.min_count("evidence_items", 2)
def draft_reply(ticket: dict, variant: str) -> dict:
    if variant == "fixed":
        return {
            "answer": "The export likely skipped invoice rows even though the job completed.",
            "evidence_items": [
                ticket["observed_signals"][1],
                ticket["observed_signals"][2],
            ],
            "next_action": "Re-run the export with invoice rows included and compare the row count before sending it.",
        }

    return {
        "answer": "The export completed, so the CSV is probably fine.",
        "evidence_items": [
            ticket["observed_signals"][0],
        ],
        "next_action": "Tell the customer to retry later.",
    }


@step("support.handoff")
@expect.required_fields(["customer_id", "reply", "audit_note"])
def package_handoff(ticket: dict, reply: dict) -> dict:
    return {
        "customer_id": ticket["customer_id"],
        "reply": reply,
        "audit_note": "Support reply must cite at least two concrete evidence items before handoff.",
    }


def run_case_study(variant: str) -> None:
    with flowguard_run(WORKFLOW):
        ticket = parse_ticket()
        reply = draft_reply(ticket, variant)
        package_handoff(ticket, reply)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the deterministic FlowGuard v1 case study.")
    parser.add_argument("--variant", choices=["broken", "fixed"], default="broken")
    args = parser.parse_args()
    run_case_study(args.variant)


if __name__ == "__main__":
    main()
