---
name: agent-readiness
description: >-
  Score how agent-ready a code repository or multi-repo workspace is,
  and apply the single highest-priority deterministic fix. Wraps the
  agent-readiness-mcp server. Use when the user asks "is this repo
  agent-ready?", "score this repo / workspace", "what should I add to
  AGENTS.md?", or "fix the top agent-readiness gap". Always call
  `enumerate_workspace` first on the user-supplied path — without that
  step scoring a parent directory of N sibling repos silently produces
  garbage numbers. The Coordination pillar (workspace-only) measures
  whether agents can operate coherently across a group of repos. The
  skill operates in two modes: **chat mode** for single repos /
  monorepos and **dashboard mode** for multi-repo workspaces, where
  per-repo scans stream live to a browser dashboard and interactive
  prompts are answered inline instead of blocking the chat.
---

# agent-readiness skill

Score how agent-ready a code repository OR a multi-repo workspace is.
The skill works in three phases:

1. **Enumerate** — call `enumerate_workspace(path)` first. Always.
2. **Classify** — read the enumeration (plus 2–3 READMEs if needed) and
   decide whether `path` is a single repo, a monorepo, a workspace of
   independents, or not a code repo at all.
3. **Scan** — route to either `scan_repo(path)` (single repo / monorepo),
   `check_workspace_readiness(path, children_paths)` (workspace, in
   chat mode), or `scan_workspace_async(path, children_paths)`
   (workspace, in dashboard mode).

The Coordination pillar (workspace-only) asks whether agents can
operate coherently across a group of repos — root AGENTS.md present,
member repos declared, dependency / change order documented. Per the
agentic-engineering literature (Mabl, Bishoy Labib), dep-graph drift
is the single most critical failure mode for multi-repo agent work.

## Choosing a mode (read this FIRST)

After Phase 2 classification, decide between two interaction modes:

| Classification          | Default mode      | Why                                                                  |
|-------------------------|-------------------|----------------------------------------------------------------------|
| single repo / monorepo  | **chat mode**     | One repo finishes in seconds; the dashboard is overkill.             |
| workspace (≥ 2 repos)   | **dashboard mode** | Per-repo scans run in parallel; the user sees live progress and can answer interactive prompts inline instead of blocking the chat for minutes. |

**Auto-force the dashboard for multi-repo workspaces.** Per
[the dashboard-mode design spec](https://github.com/harrydaihaolin/agent-readiness-research/blob/main/docs/superpowers/specs/2026-05-26-dashboard-mode-design.md#5-mode-entry-and-exit)
the skill MUST auto-launch dashboard mode for any path classified as
"workspace of independents" or multi-repo. Single-repo and monorepo
flows stay in chat mode.

**Always tell the user how to exit dashboard mode.** Either channel works:

- *In chat:* user types `/agent-readiness exit-dashboard` (or just
  asks to "exit dashboard mode") — you call `get_scan_status` to
  observe the next state and switch back to chat mode.
- *In dashboard:* user clicks the "Exit dashboard mode" button — the
  scan keeps running in the background, the dashboard server stays
  up until its idle timeout, and your next chat-side action observes
  `mode_exit_requested: true` on `get_scan_status` and reverts.

The scan is the same scan in either mode; only the surface changes.

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
| `root.has_git == false` AND ≥ 2 children with `has_git == true`                              | **workspace of independents** | Read root AGENTS.md (if any) + 2–3 child READMEs to confirm independent vs. coordinated; check whether `ontology/` exists at the workspace root — if not, **offer** the bootstrap loop (see below); then `check_workspace_readiness` |
| Any `manifest_signals.*` is `true`                                                           | **monorepo**                  | Skip child README reads; call `scan_repo(root)`                                                                                        |
| `root.has_git == true` AND no children with `.git` AND all signals false                     | **single repo**               | `scan_repo(root)`                                                                                                                      |
| Root has neither `.git` nor `README.md` AND enumeration returned zero children               | **not a code repo**           | Tell the user, exit                                                                                                                    |
| Anything else                                                                                | **ambiguous**                 | Read root + 2–3 child READMEs via the Read tool; ask the user if still unclear                                                         |

### Phase 3a — Chat mode — single repo / monorepo

```
result = scan_repo(path="/path/to/repo")
print(result["overall_score"])
print(result["top_action"])
```

The `top_action` block contains `action` (a structured edit) and
`verify` (a one-line shell command).

### Phase 3b — Chat mode — workspace (fallback)

Use `check_workspace_readiness` only when **the user explicitly opted
out of dashboard mode**. Otherwise prefer Phase 3c (dashboard mode),
which is the default for multi-repo workspaces.

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

### Phase 3c — Dashboard mode — workspace (default)

Use this for any multi-repo workspace, monorepo with many sub-repos,
or any path where you'd otherwise block the chat for >30s waiting on
sequential scans. The dashboard surfaces per-repo progress live and
lets the user answer interactive prompts inline.

```
session = scan_workspace_async(
    path="/path/to/workspace",
    children_paths=[<paths Claude classified as workspace members>],
)
# session contains: scan_id, dashboard_url, sse_url, snapshot_url
```

Then **tell the user where the dashboard is**:

- Print `session["dashboard_url"]` so they can open it in a browser.
  The bundled scan-and-view server hosts the SPA at
  `http://localhost:<port>/live/<scan_id>` (the URL above already
  points at it).
- Tell them they can **exit dashboard mode anytime** by typing
  `/agent-readiness exit-dashboard` here in the chat OR by clicking
  the "Exit dashboard mode" button in the browser. Either channel
  returns control to chat mode without killing the scan.
- Hand off — do NOT block the chat tailing the SSE stream. The skill
  bridge is **hands-off** by design (see spec § 4): you only check
  status when the user types in chat.

#### Status polling during dashboard mode

Each time the user sends a chat message while dashboard mode is
active, call `get_scan_status(scan_id)` once and respond conversationally
based on what comes back. The status envelope (enriched in
agent-readiness-mcp v0.7.0) carries:

| Field                    | What to do with it                                                   |
|--------------------------|----------------------------------------------------------------------|
| `status`                 | If `completed`, summarise and offer apply. If `running`, keep brief. |
| `progress.completed/total` | One-liner: "X of Y repos done".                                    |
| `overall_score`          | Render only when `status == completed`.                              |
| `sse_url`                | Recover the dashboard URL from this if the user lost the tab.        |
| `prompts_pending_count`  | If > 0, **tell the user to answer the prompts in the dashboard**.    |
| `mode_exit_requested`    | If `true`, switch back to chat mode (the user clicked Exit).         |

Never call `get_scan_status` in a loop. One call per chat turn — the
skill bridge is hands-off, not a live tail.

#### Mid-scan interactive prompts

The scanner asks up to six kinds of clarifying question during a scan
(classify / members / umbrella / topaction / ratify / clarify). In
dashboard mode the user answers them inline by clicking buttons in the
PromptsQueue — you do NOT need to relay the question into chat. If
`prompts_pending_count > 0` is reported and stays > 0 across several
turns, gently nudge the user to switch to the browser tab.

If the user explicitly asks for a question to be answered in chat
("just tell me what it's asking"), read it from
`fetch <snapshot_url>` (or shell out to the dashboard's POST endpoint
to submit on their behalf).

#### Exit dashboard mode in chat

When the user asks to exit dashboard mode:

```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"source": "chat"}' \
  <session["dashboard_url"]>/api/scans/<scan_id>/exit
```

The scan keeps running. Tell the user the dashboard tab is still
useful for watching progress; chat mode is back.

## Bootstrap an ontology

Use this when the user asks to **bootstrap an ontology**, **set up an ontology**,
or when you are about to score a workspace and **no `ontology/` directory**
exists at the workspace root. Ontology bootstrap is optional — offer it for
workspace-of-independents paths, never force it.

All bootstrap tools are reached via the **`ontology` passthrough** on
`agent-readiness-mcp`:

```
ontology(subcmd="<tool_name>", arguments={...})
```

### Propose / ratify lifecycle

Every atom carries `lifecycle: {state: proposed | ratified, …}`. Bootstrap
tools **propose** atoms; a human must **ratify** each accepted atom via CLI.
Re-bootstrap is **additive only** — ratified atoms are never overwritten.

**Ratification is human-gated by default.** Do not auto-ratify unless the
user explicitly opts in.

After each ratification batch, run the closure invariant:

```bash
agent-readiness ontology validate ontology/ --strict
```

Ratified atoms must not reference unratified atoms.

### Bootstrap loop (6 steps)

1. **`bootstrap_init`** — scaffold the starter ontology skeleton.

   ```
   ontology(subcmd="bootstrap_init", arguments={"path": "/abs/path", "profile": "workspace"})
   ```

   Profiles: `workspace` (default), `single-repo`, `monorepo`.

2. **Object instances** — propose Repos, then repeat for each Object Type.

   ```
   ontology(subcmd="bootstrap_propose_object_instances", arguments={"path": "/abs/path", "object_type": "Repo"})
   ```

   Repeat for `Library`, `Protocol`, `RulesPack`.

   **Human gate:** present `proposed` and `ambiguities` from the envelope.
   Resolve any `???` markers with the user. For each accepted atom:

   ```bash
   agent-readiness ontology ratify --atom <id> --ratified-by <handle>
   ```

3. **Link instances** — after ≥ 80% of Repo instances are ratified, propose
   links for each Link Type:

   ```
   ontology(subcmd="bootstrap_propose_link_instances", arguments={"path": "/abs/path", "link_type": "dependsOn"})
   ```

   Repeat for: `partOf`, `ownedBy`, `vendors`, `providesProtocol`,
   `consumesProtocol`, `deploysTo`, `releasedAs`. Same ratify cadence as step 2.

4. **Interface claims** — evaluate satisfaction proofs for each declared
   Interface:

   ```
   ontology(subcmd="bootstrap_propose_interface_claims", arguments={"path": "/abs/path", "interface": "Releasable"})
   ```

   Repeat for: `Headless`, `Versioned`, `Scannable`, `Documented`, `Tested`.

5. **Function implementations** — generate Python stubs for declared Functions:

   ```
   ontology(subcmd="bootstrap_propose_function_implementations", arguments={"path": "/abs/path", "function_type": "compute_dep_graph"})
   ```

   Repeat for: `compute_publish_order`, `compute_change_impact`.

6. **Action / Intent types** — detect Actions from CI workflows and emit Intent
   templates:

   ```
   ontology(subcmd="bootstrap_propose_action_intent_types", arguments={"path": "/abs/path", "scope": "all"})
   ```

   Scope values: `all` (default), `single_system`, `cross_repo`.

### Example: user says "bootstrap an ontology for this workspace"

```
1. ontology(subcmd="bootstrap_init", arguments={"path": "/abs/path", "profile": "workspace"})
   → confirm files_written ≥ 25, present to user.

2. ontology(subcmd="bootstrap_propose_object_instances", arguments={"path": "/abs/path", "object_type": "Repo"})
   → present envelope.proposed and envelope.ambiguities to user. Each proposed atom
     shows lifecycle.confidence and any `???` markers.

3. For each accepted Repo: agent-readiness ontology ratify --atom <repo_id> --ratified-by <user>.
   Then validate: agent-readiness ontology validate ontology/ --strict.
```

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
