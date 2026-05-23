---
name: agent-readiness
description: >-
  Score how agent-ready a code repository or multi-repo workspace is, and
  apply the single highest-priority deterministic fix. Wraps the
  agent-readiness-mcp server. Use when the user asks "is this repo
  agent-ready?", "score this repo / workspace", "what should I add to
  AGENTS.md?", or "fix the top agent-readiness gap". Always call
  `enumerate_workspace` first on the user-supplied path — without that
  step scoring a parent directory of N sibling repos silently produces
  garbage numbers. The Coordination pillar (workspace-only) measures
  whether agents can operate coherently across a group of repos.
---

# agent-readiness skill

Score how agent-ready a code repository OR a multi-repo workspace is.
The skill works in three phases:

1. **Enumerate** — call `enumerate_workspace(path)` first. Always.
2. **Classify** — read the enumeration (plus 2–3 READMEs if needed) and
   decide whether `path` is a single repo, a monorepo, a workspace of
   independents, or not a code repo at all.
3. **Scan** — route to either `scan_repo(path)` (single repo / monorepo)
   or `check_workspace_readiness(path, children_paths)` (workspace).

The Coordination pillar (workspace-only) asks whether agents can
operate coherently across a group of repos — root AGENTS.md present,
member repos declared, dependency / change order documented. Per the
agentic-engineering literature (Mabl, Bishoy Labib), dep-graph drift
is the single most critical failure mode for multi-repo agent work.

## Workflow

### Phase 1 — Enumerate

Always start with `enumerate_workspace(path)`. Never call `scan_repo`
first on an unfamiliar path. The enumeration is cheap, static, and
gives you enough to classify.

```
result = enumerate_workspace(path="/path/to/dir")
```

The envelope contains `root`, `children[]`, `manifest_signals`, and
`stats`. Read it all.

### Phase 2 — Classify

Apply this rubric in order:

| Signal                                                                                       | Classification                | Next step                                                                                                                              |
|----------------------------------------------------------------------------------------------|-------------------------------|----------------------------------------------------------------------------------------------------------------------------------------|
| `root.has_git == false` AND ≥ 2 children with `has_git == true`                              | **workspace of independents** | Read root AGENTS.md (if any) + 2–3 child READMEs to confirm independent vs. coordinated; then `check_workspace_readiness`              |
| Any `manifest_signals.*` is `true`                                                           | **monorepo**                  | Skip child README reads; call `scan_repo(root)`                                                                                        |
| `root.has_git == true` AND no children with `.git` AND all signals false                     | **single repo**               | `scan_repo(root)`                                                                                                                      |
| Root has neither `.git` nor `README.md` AND enumeration returned zero children               | **not a code repo**           | Tell the user, exit                                                                                                                    |
| Anything else                                                                                | **ambiguous**                 | Read root + 2–3 child READMEs via the Read tool; ask the user if still unclear                                                         |

### Phase 3a — Scan a single repo / monorepo

```
result = scan_repo(path="/path/to/repo")
print(result["overall_score"])
print(result["top_action"])
```

The `top_action` block contains `action` (a structured edit) and
`verify` (a one-line shell command).

### Phase 3b — Scan a workspace

```
result = check_workspace_readiness(
    path="/path/to/workspace",
    children_paths=[<paths Claude classified as workspace members>],
)
```

The envelope contains 5 pillars (Cognitive Load, Feedback, Flow,
Safety — aggregated from children; Coordination — workspace-only),
per-child cards sorted worst-first, and a single `top_action` whose
`scope` is `"workspace"` (a Coordination fix) or `"child"` (the worst
child's top_action with `child_path` stamped on).

Present:

- One-line workspace overall score + 5 pillar scores.
- Children sorted worst-first, each with overall score + safety cap if any.
- The `top_action` with its `scope` called out.
- The verify command, so the user can confirm the fix.

## Apply contract

`apply_top_action` covers `create_file`, `append_to_file`, and the
other structured action kinds. `run_command` actions are surfaced for
the user to execute manually — the skill never runs them. This is
intentional: it closes the footgun where a `git init && git add -A`
recipe would have been auto-executed against a workspace and produced
broken gitlinks.

## Anti-patterns

- **Never call `scan_repo` on a path you haven't enumerated**, unless
  the user explicitly named the path and it passes a quick `.git/`
  check.
- **Never call `check_workspace_readiness` with an empty
  `children_paths`** — the tool will refuse, and rightly so. Classify
  first.
- **Never auto-run `run_command` actions.** Surface them; let the user
  execute.

## When NOT to use this skill

- The user wants you to write code that uses the agent-readiness
  library (use the docstrings, not this skill).
- The repo is brand-new (< 24h old, 0 commits beyond the initial). The
  Coordination checks won't fire usefully on an empty workspace.

## Worked example (the dogfood case)

User invokes the skill on `agent-readiness_project/`.

1. `enumerate_workspace("agent-readiness_project")` returns:
   - `root.has_git: false`, `root.has_agents_md: true`
   - 17 children, all with `has_git: true`
   - All `manifest_signals` false
2. Rubric → **workspace of independents**.
3. Read root AGENTS.md (confirms portfolio context). Spot-check 2 child READMEs.
4. `check_workspace_readiness("agent-readiness_project", [<17 child paths>])`.
5. Returns: 5-pillar envelope. If Coordination fires (root AGENTS.md
   present but no `## Repos in this workspace` section, no dep graph
   documented) the top_action is `scope="workspace"`,
   `check_id="coordination.dep_graph"`, with a structured
   `append_to_file` action targeting root AGENTS.md.
6. Skill presents the report. User reviews, optionally calls
   `apply_top_action`.
