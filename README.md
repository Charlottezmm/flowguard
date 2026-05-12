# FlowGuard

**Workflow context bridge for AI coding agents.**

Your AI workflow says `success`. FlowGuard helps your coding agent understand what actually happened.

## Problem

AI coding agents can read code, but they often miss the workflow context humans keep in their head: which step produced which artifact, what the last run returned, which API response was empty, and which downstream step will break next.

FlowGuard turns messy workflow state into structured context for agents and readable repair reports for humans.

## What It Does

- Builds a lightweight `workflow_map.json` for AI workflow projects.
- Records run facts such as step inputs, outputs, failures, and impacted downstream steps.
- Generates `agent_context.md`, a compact repair context for Codex, Claude Code, Cursor, and similar agents.

## Agent Usage

```text
Use FlowGuard to map this workflow, inspect the failed run, and create a repair context.
```

## Example Output

```md
# Agent Context

Failed step: storyboard.generate

Failed checks:
- shots must contain at least 5 items
- shot_03 missing vo_text

Downstream impacted:
- image_prompts.generate
- voiceover.generate
- video.render

Relevant files:
- workflows/video.py
- schemas/storyboard.json
- prompts/storyboard.md

Suggested focus:
Check prompt constraints and schema mapping.
```

## Status

FlowGuard is experimental. v0.1 focuses on Python AI workflows, local artifacts, and Skill-first usage.

## Roadmap

- v0.1: Skill draft, Python runtime, workflow map, trace, agent context.
- v0.2: API/file checks, golden runs, minimal MCP query layer.
- v1.0: stable Skill + runtime + MCP, run comparison, real-world case study.

