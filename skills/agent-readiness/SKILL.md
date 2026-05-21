---
name: agent-readiness
description: >-
  Use this skill to score how AI-ready a code repository (or every repo in
  a multi-repo workspace) is and to apply the single highest-priority
  deterministic fix. Useful when the user asks "is this repo agent-ready?",
  "score this workspace", "what should I add to AGENTS.md?", "fix the top
  agent-readiness gap", or starts work in an unfamiliar checkout and wants
  the canonical commands and boundary rules summarised. Always call
  `detect_workspace` first on the user-supplied path — without that step
  scoring a parent directory of N sibling repos produces silently garbage
  numbers. Wraps the agent-readiness-mcp server, which is itself backed by
  the agent-readiness scanner wheel.
---

The agent-readiness skill scores a repo on four pillars (Cognitive Load,
Feedback, Flow, Safety) and pins the single highest-priority structured
fix as the `top_action`. The skill works in three phases:

1. **Detect** what kind of path the user handed you (single repo,
   monorepo, multi-repo workspace). Without this step, scoring a parent
   directory of N sibling repos silently produces garbage numbers.
2. **Scan** the right repo (or N repos, with the user's selection if
   they didn't pre-pick) and read the `top_action` block.
3. **Apply** the pinned action (`apply_top_action`) and run its verify
   command. The action is deterministic — there is no LLM in the apply
   path.

## Workflow

### 1. Always call `detect_workspace` first

Before any scan, classify the user-supplied path:

```
detection = detect_workspace(path="/path/to/something")
print(detection["classification"])  # single_repo | monorepo | multi_repo_workspace
print(detection["confidence"])      # high | medium | low
```

Branch on `classification`:

- **`single_repo`** — silently proceed to `scan_repo` (no HITL prompt;
  this is the most common case and the path the user expects).
- **`monorepo`** — narrate it briefly: *"Monorepo detected (signal:
  `<detection['signals']['fired'][0]>`). Scanning as one repo."* Then
  call `scan_repo`. The scanner today scores monorepos as one repo by
  design; per-package breakdowns are a future feature.
  - For `confidence: low` (Signal C — scattered manifests), soften it:
    *"This might be a monorepo (3+ scattered manifests). Treating as a
    single repo — let me know if you want me to scan a sub-package
    directly instead."*
- **`multi_repo_workspace`** — never auto-scan. Narrate the list and
  ask the user which subset to scan. See the next section.

### 2a. Single-repo scan

```
result = scan_repo(path="/path/to/repo")
print(result["overall_score"])
print(result["top_action"])
```

The `overall_score` is on a 0-100 scale; treat anything below 90 as
"ship a fix" and below 60 as "this repo isn't agent-ready yet, expect
the apply loop to iterate."

The `top_action` payload contains:

- `check_id`, `pillar`, `severity`, `weight`, `rationale` — why this
  finding wins the pin
- `action` — the structured edit (`kind`: create_file / append_to_file /
  edit_gitignore / insert_after / modify_manifest_field / run_command /
  multi_step)
- `verify` — a one-line shell command that confirms the fix landed
- optional `fix_hint` — human-readable prose for cases where the
  structured action isn't enough on its own

### 2b. Multi-repo workspace selection

Narrate the detected repos with their AGENTS.md descriptions (if
present), then ask the user which to scan. Example narration when the
detector returns 3 repos with display names:

> I see this is a multi-repo workspace (confidence: high) with 3
> sibling repos:
>
> 1. `alpha-svc` — Alpha HTTP service.
> 2. `beta-lib` — Beta shared library.
> 3. `gamma-cli` — Gamma command-line client.
>
> Scan all three, or just a subset?

If the user says "all," call `scan_workspace(path, select=None)`. If
they pick a subset, pass `select=["alpha-svc", "gamma-cli"]`. Names
must match the `name` field from `detect_workspace`'s `repos` array
exactly; the tool surfaces unknown names in `skipped` with
`reason="not detected"`, which you should re-raise as a clean error
to the user instead of silently proceeding.

If the detection returned **drift warnings** (the user's `AGENTS.md`
mentions a repo that isn't checked out, or a checked-out repo isn't
listed in `AGENTS.md`), surface them at the end of the narration as a
"by the way" — they're a free maintenance signal, not a hard error:

> By the way: `AGENTS.md` mentions `./delta-not-checked-out` but
> there's no `.git` for it on disk. Probably worth either checking it
> out or updating `AGENTS.md`.

The result of `scan_workspace` is a single envelope with a `scanned`
list (one entry per repo, each containing a full `ReadinessReport`
under `report`) and a `skipped` list. Iterate the `scanned` entries
when narrating per-repo summaries to the user.

### `scan_repo` on a multi-repo workspace

If the user (or you, by mistake) calls `scan_repo` on a workspace
root, the tool returns a structured `error` payload instead of a
report:

```
{
  "error": "multi_repo_workspace",
  "hint": "this path contains multiple repos; call detect_workspace(path) to list them or scan_workspace(path, select=[...]) to scan a subset",
  "detected_repos": ["alpha-svc", "beta-lib", "gamma-cli"],
  "root": "...",
  "version": "detect_v1"
}
```

Treat this as a "switch tools" signal — don't try to apologise to the
user about the missing report; just chain through to
`scan_workspace` (or back to `detect_workspace` if the user needs to
pick) without ceremony.

### 3. Apply the fix

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

### 4. Iterate

For repos starting below 90, expect 2-5 apply loops. After each apply,
re-scan; the top_action will rotate to the next-highest-priority fix.
On a multi-repo workspace, iterate per repo — don't try to apply a
single top_action across multiple sibling repos.

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

This skill ships as a Claude Code plugin, which auto-wires the
`agent-readiness-mcp` MCP server for you. Users on other harnesses
install the bare SKILL.md plus a manual MCP config.

### Claude Code (plugin)

```
/plugin marketplace add harrydaihaolin/agent-readiness-skill
/plugin install agent-readiness@agent-readiness-skill
```

Once installed and `agent-readiness-mcp` is on your `$PATH`
(`pip install agent-readiness-mcp`), the skill auto-triggers when you
ask Claude things like "score this repo for agent readiness."

### Cursor / Claude Desktop (bare SKILL.md)

```
git clone https://github.com/harrydaihaolin/agent-readiness-skill.git
cd agent-readiness-skill
./scripts/install.sh             # auto-detects Cursor / Claude Desktop dirs
```

The script copies this SKILL.md into the right harness skills directory.
You still need to paste the MCP server JSON into your harness config
(`~/.cursor/mcp.json` for Cursor; `~/.claude/claude_desktop_config.json`
for Claude Desktop). The script prints the exact payload at the end.
