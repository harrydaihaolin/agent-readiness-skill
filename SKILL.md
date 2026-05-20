---
name: agent-readiness
description: >-
  Use this skill to score how AI-ready a code repository is and to apply the
  single highest-priority deterministic fix. Useful when the user asks "is
  this repo agent-ready?", "what should I add to AGENTS.md?", "score this
  repo", "fix the top agent-readiness gap", or starts work in an unfamiliar
  repo and wants the canonical commands and boundary rules summarised. Wraps
  the agent-readiness-mcp server, which is itself backed by the
  agent-readiness scanner wheel.
---

The agent-readiness skill scores a repo on four pillars (Cognitive Load,
Feedback, Flow, Safety) and pins the single highest-priority structured
fix as the `top_action`. The skill works in two phases:

1. Read the report (`scan_repo`) and decide whether the score is acceptable.
2. If a fix is warranted, apply the pinned action (`apply_top_action`) and
   run its verify command. The action is deterministic — there is no LLM
   in the apply path.

## Workflow

### 1. Run a scan first

Always start with `scan_repo` and read the `top_action` block. The
`overall_score` is on a 0-100 scale; treat anything below 90 as "ship a
fix" and below 60 as "this repo isn't agent-ready yet, expect the apply
loop to iterate."

```
result = scan_repo(path="/path/to/repo")
print(result["overall_score"])
print(result["top_action"])
```

The `top_action` payload contains:

- `check_id`, `pillar`, `severity`, `weight`, `rationale` — why this
  finding wins the pin
- `action` — the structured edit (`kind`: create_file / append_to_file /
  edit_gitignore / insert_after / modify_manifest_field / run_command /
  multi_step)
- `verify` — a one-line shell command that confirms the fix landed
- optional `fix_hint` — human-readable prose for cases where the
  structured action isn't enough on its own

### 2. Apply the fix

When the user asks "fix the top issue" or "make this agent-ready," call
`apply_top_action(path, run_verify=True)`. The tool:

- refuses to overwrite existing files unless the action's
  `preconditions` explicitly allow it
- runs the verify command after applying and reports whether it passed
- never commits, never opens a PR — that's the human's call

Read the returned envelope:

- `applied: true` + `verified: true` → tell the user the fix landed and
  what file you wrote
- `applied: true` + `verified: false` → report the verify stderr; the
  fix may still be correct but the verify command is too strict
- `applied: false` → read `skipped_reason`; usually a precondition the
  user can satisfy, or a `run_command` action whose contract is "I tell
  you the command, you run it"

### 3. Iterate

For repos starting below 90, expect 2-5 apply loops. After each apply,
re-scan; the top_action will rotate to the next-highest-priority fix.

## When NOT to use this skill

- The user wants you to write code that uses the agent-readiness library
  (use the docstrings, not this skill).
- The repo is brand-new (< 24h old, 0 commits beyond the initial). Many
  rules are not informative on a one-commit repo; suggest the user run
  `agent-readiness gen agents-md` first to seed the canonical files.

## Output format

When showing the user a scan result, prefer:

```
Score: 72.5 / 100 (band: silver)

Pillar breakdown:
  Cognitive Load: 80
  Feedback: 65
  Flow: 70
  Safety: 90 (no cap applied)

Top action (Phase: feedback)
  Add a CI workflow that runs the test suite.
  Verify: rg -q -e 'on:|jobs:' .github/workflows/ 2>/dev/null
```

Always surface the verify command — it lets the user (or the next
agent) confirm the fix without re-running the whole scanner.

## Installation

The skill works in Claude (Claude Code, Claude Desktop) and Cursor — both
consume the same SKILL.md open-standard format.

### 1. Install the MCP server

```bash
pip install agent-readiness-mcp
```

### 2. Drop SKILL.md into your skills directory

- **Claude**: `~/.claude/skills/agent-readiness/SKILL.md`
- **Cursor (user-level)**: `~/.cursor/skills/agent-readiness/SKILL.md`
- **Cursor (project-level)**: `.cursor/skills/agent-readiness/SKILL.md`

The repo's `scripts/install.sh` does steps 1 and 2 for you and auto-detects
which harnesses you have:

```bash
./scripts/install.sh                  # auto-detect
./scripts/install.sh --target=claude  # force Claude only
./scripts/install.sh --target=cursor  # force Cursor only
./scripts/install.sh --target=both    # both, creating dirs if needed
```

### 3. Wire the MCP server into your harness config

Same JSON payload for both harnesses:

```json
{
  "mcpServers": {
    "agent-readiness": {
      "command": "agent-readiness-mcp",
      "args": ["--transport", "stdio"]
    }
  }
}
```

Paste into:

- **Claude Desktop / Claude Code**: `~/.claude/claude_desktop_config.json`,
  or run `claude mcp add agent-readiness -- agent-readiness-mcp --transport stdio`.
- **Cursor (user-level)**: `~/.cursor/mcp.json`.
- **Cursor (project-level)**: `.cursor/mcp.json` inside the repo.

Restart the harness to pick up the new server.
