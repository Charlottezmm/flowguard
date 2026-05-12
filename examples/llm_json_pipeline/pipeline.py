from flowguard import expect, step


@step("profile.extract")
@expect.required_fields(["name", "audience", "selling_points"])
def extract_profile(raw_text: str) -> dict:
    return {
        "name": "Demo Product",
        "audience": "indie developers",
        "selling_points": ["local-first", "agent-readable context"],
    }


@step("hooks.generate")
@expect.min_count("hooks", 5)
def generate_hooks(profile: dict) -> dict:
    return {
        "hooks": [
            "Your workflow says success, but is it right?",
            "Stop explaining the same bug to your AI agent.",
            "Give coding agents the workflow context they miss.",
        ]
    }


def main() -> None:
    profile = extract_profile("FlowGuard demo product")
    generate_hooks(profile)


if __name__ == "__main__":
    main()

