---
name: agent-readiness
description: >-
  Score how agent-ready a code repository, monorepo, or multi-repo
  workspace is, and surface the fixes as paste-ready prompts — entirely
  in chat, no browser or dashboard. Wraps the agent-readiness-mcp
  server (>= 0.9.0). Use when the user asks "is this repo agent-ready?",
  "score this repo / workspace", "what should I add to AGENTS.md?", or
  "fix the top agent-readiness gap". The first tool call on any
  user-supplied path is always **`inspect_tool(path)`** — it returns the
  suggested workspace type in ~200ms with zero deliberation on your
  side. Then call exactly ONE headless scan tool, which returns the
  readiness report inline: `scan_repo_tool(path)` (single_repo),
  `scan_monorepo_tool(path)` (monorepo), or
  `scan_workspace_tool(path, children)` (workspace, where children is
  the list of `.git` repo paths from inspect). Present the score plus
  the engine's generated `fix_prompt`s in chat — for a workspace the
  headline output is the Coordination prompts. Offer to apply the top
  fix (`apply_top_action_tool`) or to write a root `AGENTS.md`. The
  Coordination pillar (workspace-only) measures whether agents can
  operate coherently across a group of repos.
---

# agent-readiness skill

Score how agent-ready a code repository, monorepo, or multi-repo
workspace is — and generate the fixes as paste-ready prompts. This
skill is **prompt-only**: everything happens in chat. There is no
browser, no dashboard, and no background scan to babysit.

## The contract

**Two tool calls on a fresh user request: classify, then scan.**

1. `inspect_tool(path)` — returns `{enumeration, classification}` in ~200ms.
2. Exactly ONE headless scan tool, picked by `classification.suggested_type`.
   Each returns the readiness report **inline** — you read it and respond.

**You make ZERO classification decisions.** The classifier is a
deterministic rubric in the engine. If you find yourself thinking "but
maybe this monorepo is actually a workspace because…" — stop. Trust
`suggested_type` and call the matching tool.

## Workflow

### Phase 1 — Always call `inspect_tool` first

```
result = inspect_tool(path="/path/to/anything")
```

Returns:

```json
{
  "enumeration": {
    "root": "...",
    "root_has_git": true | false,
    "repos": [ { "path": "...", "has_git": true }, ... ],
    "directories_walked": 142,
    "elapsed_ms": 64
  },
  "classification": {
    "suggested_type": "single_repo" | "monorepo" | "workspace",
    "confidence": "high" | "medium" | "low",
    "rationale": "Root has no .git, 7 nested .git."
  }
}
```

If `inspect_tool` returns `{"status": "error"}` (bad path, etc.), surface the
`error` message to the user verbatim and stop. Otherwise proceed to Phase 2.

### Phase 2 — Dispatch on `classification.suggested_type`

| `suggested_type`   | Call                                              | Returns                                  |
|--------------------|---------------------------------------------------|------------------------------------------|
| `"single_repo"`    | `scan_repo_tool(path)`                            | `ReadinessReport` (one repo)             |
| `"monorepo"`       | `scan_monorepo_tool(path)`                        | `ReadinessReport` (root scored as one)   |
| `"workspace"`      | `scan_workspace_tool(path, children=[...])`       | `WorkspaceReadinessReport` (incl. Coordination) |

For a workspace, build `children` from the inspect enumeration: the
list of `repos[*].path` entries that have `.git`. Pass them explicitly —
the tool trusts your selection and does not re-enumerate.

Each scan runs synchronously and returns the report inline. There is no
`dashboard_url` to print and nothing to hand off — read the report and
move to Phase 3.

### Phase 3 — Present the score and generate fix-prompts

This is the whole point of the skill: turn the report into paste-ready
prompts the user (or another agent) can act on.

**Single repo / monorepo:**

1. State the overall score and the per-pillar scores.
2. Call `list_friction_tool(path)` — it returns every WARN/ERROR finding
   with a paste-ready `fix_prompt`, sorted by `score_impact`. Present the
   top few as prompts, each with its `verify` command.
3. Offer to apply the single highest-impact fix with
   `apply_top_action_tool(path)`.

**Workspace:**

1. State the overall score + every per-pillar score in the report
   (Cognitive Load, Feedback, Flow, Safety, and the workspace-only
   **Coordination** pillar; some engine versions also report Ontology).
2. List the children worst-first with their scores.
3. Surface the report's `top_action`. If it carries a `fix_prompt` —
   for a workspace this is usually the **Coordination** prompt (e.g.
   "add a root `AGENTS.md` declaring member repos and dependency
   order") — present it with its `verify`. If `top_action` has no
   `fix_prompt`, present its `message`/`action` instead.
4. Offer to write the root `AGENTS.md` yourself, or to drill into the
   worst child with `scan_repo_tool` + `list_friction_tool`.

Never invent scores or prompts. Everything you present comes from the
report or `list_friction_tool`.

## Tool reference

| Tool                          | When                                                              |
|-------------------------------|-------------------------------------------------------------------|
| `inspect_tool`                | Always first. ~200ms. Returns enumeration + classification.       |
| `scan_repo_tool`              | When `suggested_type == "single_repo"`. Returns report inline.    |
| `scan_monorepo_tool`          | When `suggested_type == "monorepo"`. Returns report inline.       |
| `scan_workspace_tool`         | When `suggested_type == "workspace"`. Pass `children=[...]`.       |
| `list_friction_tool`          | Phase 3: every WARN/ERROR finding with a paste-ready `fix_prompt`. |
| `apply_top_action_tool`       | When the user accepts the top fix.                                 |

There is no dashboard tool. The MCP server is headless and prompt-only;
do not look for a `scan_workspace_async_tool`, `get_scan_status_tool`,
or any `dashboard_url` — they were removed in MCP 0.9.0.

## The Coordination pillar (workspace-only)

Multi-repo workspaces add a **Coordination** pillar on top of the
per-repo pillars. It asks whether agents can operate coherently across
a group of repos:

- Is there a root `AGENTS.md` declaring member repos and boundaries?
- Are dependency-update orders documented?
- Are coupling pairs annotated (so changing one ratchets the other)?

Coordination is the single most critical failure mode for multi-repo
agent work per the agentic-engineering literature (Mabl 2024 "AI agents
across services", Bishoy Labib "Coordination gaps in multi-repo dev
environments"). Lead with its `fix_prompt` when presenting a workspace.

## Quick examples

**User: "score ~/code/llm-eval"**

```
inspect_tool(path="/home/user/code/llm-eval")
# → {classification: {suggested_type: "single_repo", confidence: "high"}}

scan_repo_tool(path="/home/user/code/llm-eval")
# → {overall_score: 72.0, pillars: [...], top_action: {...}}

list_friction_tool(path="/home/user/code/llm-eval")
# → [{rule_id, severity, message, fix_prompt, verify, score_impact}, ...]
```

Response: "Overall 72/100. Top gaps and paste-ready fixes: …" then offer
`apply_top_action_tool`.

**User: "is ~/mle agent-ready?"** (a folder containing 7 nested git projects)

```
inspect_tool(path="/home/user/mle")
# → {classification: {suggested_type: "workspace", confidence: "medium",
#                     rationale: "Root has no .git, 7 nested .git."},
#    enumeration: {repos: [{path: ".../r1", has_git: true}, ...]}}

scan_workspace_tool(
    path="/home/user/mle",
    children=["/home/user/mle/r1", ".../r2", ".../r3", ...],
)
# → {overall_score, pillars: [..., {pillar: "coordination", ...}],
#    children: [...], top_action: {fix_prompt: "...", verify: "..."}}
```

Response: lead with the 5 pillar scores, then the Coordination
`fix_prompt`; offer to write the root `AGENTS.md`.

**User: "score this monorepo"** (root has `.git`, two packages inside)

```
inspect_tool(path=".")
# → {classification: {suggested_type: "monorepo"}}

scan_monorepo_tool(path=".")
# → {overall_score, pillars, top_action}
```
