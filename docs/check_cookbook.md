# FlowGuard Check Cookbook

Checks should encode intent. A check is useful when it would fail on a bad
workflow output that could otherwise look like success.

Use these examples as starting points, then adapt them to the real workflow
contract.

## LLM Output

Use this when a model returns structured data for a downstream step.

```python
@step("issue.triage")
@expect.required_fields(["issue_type", "severity", "repro_steps", "affected_files"])
@expect.min_count("repro_steps", 2)
@expect.min_count("affected_files", 1)
def triage_issue(issue: dict) -> dict:
    return call_model_for_triage(issue)
```

Intent: the triage output must contain enough reproduction detail and affected
file context for a coding agent to act.

Weak check to avoid:

```python
@expect.non_empty("issue_type")
```

That may pass while the model still omits the evidence a repair step needs.

## API Response

Use this when workflow code already captured a response-like object. FlowGuard
does not make HTTP requests for these checks.

```python
@step("customer.fetch")
@expect.response_status("response", min=200, max=299)
@expect.response_required_fields("response.json", ["id", "plan", "status"])
@expect.no_error_envelope("response.json")
def fetch_customer(customer_id: str) -> dict:
    response = client.get_customer(customer_id)
    return {"response": response}
```

Intent: the response must be successful and contain the fields later steps need.

Weak check to avoid:

```python
@expect.non_empty("response")
```

That does not prove the API call succeeded or returned a usable body.

## File Artifact

Use this when a step returns a path to a generated local file.

```python
@step("report.write")
@expect.file_exists("artifact.path")
@expect.file_non_empty("artifact.path")
@expect.file_extension("artifact.path", [".md"])
def write_report(data: dict) -> dict:
    path = render_report(data)
    return {"artifact": {"path": path}}
```

Intent: the workflow produced the expected file artifact and it is not empty.

Weak check to avoid:

```python
@expect.file_exists("artifact.path")
```

By itself, existence can pass for an empty or stale file.

## JSON Artifact

Use this when a step writes JSON that another tool or agent will read.

```python
@step("facts.write")
@expect.file_exists("artifact.path")
@expect.file_valid_json("artifact.path")
def write_facts(result: dict) -> dict:
    path = save_json_artifact(result)
    return {"artifact": {"path": path}}
```

Intent: the handoff file exists and parses as JSON before downstream consumers
trust it.

Weak check to avoid:

```python
@expect.file_non_empty("artifact.path")
```

Non-empty text can still be invalid JSON.

## Downstream Dependency Failure

Use this when a downstream step fails because an upstream handoff is incomplete.
Put the check on the upstream output, where the bad data first appears.

```python
@step("search.collect")
@expect.min_count("results", 3)
@expect.required_fields("results[]", ["title", "url", "snippet"])
def collect_search_results(query: str) -> dict:
    return run_search(query)


@step("brief.create")
def create_brief(search: dict) -> dict:
    return summarize_results(search["results"])
```

Intent: `brief.create` needs enough search evidence to produce a useful brief.
The check belongs on `search.collect`, not on the downstream summary after the
evidence has already been lost.

Weak check to avoid:

```python
@expect.non_empty("results")
```

One result with no URL or snippet is not enough for the downstream step.
