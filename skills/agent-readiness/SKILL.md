---
name: agent-readiness
description: >-
  Score how agent-ready a code repository or multi-repo workspace is,
  and apply the single highest-priority deterministic fix. Wraps the
  agent-readiness-mcp server. Use when the user asks "is this repo
  agent-ready?", "score this repo / workspace", "what should I add to
  AGENTS.md?", or "fix the top agent-readiness gap". The first tool
  call on any user-supplied path is always **`scan_and_view(path)`**
  (agent-readiness-mcp 0.7.4+) — it auto-classifies, auto-launches
  the dashboard, and returns the URL within ~2 seconds. The skill
  makes ZERO classification decisions and ZERO pre-flight tool calls.
  Single repos, monorepos, and multi-repo workspaces all flow through
  the same dashboard surface. The only branching is on the
  `status` field of the response: `started` → share URL; 
  `needs_disambiguation` → paint the pre-rendered prompt, re-call
  with `treat_as`; `not_a_code_repo` → tell the user, stop. The
  Coordination pillar (workspace-only) measures whether agents can
  operate coherently across a group of repos.
---

# agent-readiness skill

Score how agent-ready a code repository OR a multi-repo workspace is.

**The rule.** First tool call on any user-supplied path is **always**
`scan_and_view(path)`. The tool auto-classifies, auto-launches the
dashboard, and returns a `dashboard_url` within ~2 seconds. No
pre-flight enumeration, no classification rubric in your head, no
thinking turn between the user's message and the URL. Single repos,
monorepos, and multi-repo workspaces all flow through the same
surface — the dashboard renders a workspace-of-one for single repos
and a grid for workspaces.

Then branch on `result["status"]` (Phase 2). Four cases: `started`,
`needs_disambiguation`, `not_a_code_repo`, `invalid_input`. Done.

The Coordination pillar (workspace-only) asks whether agents can
operate coherently across a group of repos — root AGENTS.md present,
member repos declared, dependency / change order documented. Per the
agentic-engineering literature (Mabl, Bishoy Labib), dep-graph drift
is the single most critical failure mode for multi-repo agent work.

**Always tell the user how to exit dashboard mode** (after Phase 2
prints the URL). Either channel works: in chat (`/agent-readiness
exit-dashboard`) or in the browser (the "Exit dashboard mode" button).
Either channel returns control to chat without killing the scan.

## Workflow

### Phase 1 — Call `scan_and_view(path)` immediately

The first tool call on any user-supplied path is **always**
`scan_and_view(path)`. No pre-flight enumeration, no rubric in your
head, no thinking. The tool auto-classifies, auto-launches the
dashboard, and returns within ~2 seconds.

```
result = scan_and_view(path="/path/to/anything")
```

The envelope has a `status` field that tells you what happened.
Branch on it. There are exactly four outcomes:

| `result["status"]`         | What it means                                                            | What you do                                                                                                 |
|----------------------------|--------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------|
| `"started"`                | Dashboard is up. Single repo / monorepo / workspace — all the same here. | Phase 2 below. Print `dashboard_url` verbatim, hand off, stop calling tools.                                  |
| `"needs_disambiguation"`   | Signals are ambiguous; prompt is pre-rendered. NO scan started yet.       | Phase 2.5 below. Paint the prompt verbatim, wait for the user, re-call `scan_and_view(path, treat_as=...)`.   |
| `"not_a_code_repo"`        | No .git, no README, no children.                                          | Tell the user verbatim from `result["message"]`, stop.                                                       |
| `"invalid_input"` / error  | Bad path or bad `treat_as` value.                                         | Surface the error message to the user, stop.                                                                  |

### Phase 2 — When `status == "started"`

Same envelope shape as the old `scan_workspace_async`:
`dashboard_url`, `scan_id`, `pid`, `children_total`,
`eta_minutes_estimate`. Print `dashboard_url` to the user in your
very next response, then **stop calling tools**. Examples:

- Single repo: dashboard shows one card scanning live (finishes in
  seconds).
- Monorepo: dashboard shows one card (the root) scanning.
- Multi-repo workspace: dashboard shows the grid of repos scanning
  in parallel; prompts queue surfaces clarifying questions inline.

Tell the user how to exit dashboard mode (browser button or
`/agent-readiness exit-dashboard` in chat). Then yield. See Phase 3
below for status polling rules.

### Phase 2.5 — When `status == "needs_disambiguation"`

The scanner pre-rendered the chat prompt for you. **Paint it
verbatim. Do not improvise wording. Do not read READMEs to "double
check"** — READMEs do not resolve workspace-vs-monorepo questions
because every layout has READMEs. The user is the only oracle.

```text
{result["ambiguity_reason"]}

Which best describes this path?

(a) {result["ambiguity_options"][0]["label"]} — {result["ambiguity_options"][0]["hint"]}
(b) {result["ambiguity_options"][1]["label"]} — {result["ambiguity_options"][1]["hint"]}
(c) {result["ambiguity_options"][2]["label"]} — {result["ambiguity_options"][2]["hint"]}
```

Wait for the user to pick. Then re-call `scan_and_view` with
`treat_as` set to the chosen option's `id`:

```
result = scan_and_view(path=path, treat_as=<option.id>)
# Valid treat_as values: "workspace", "monorepo", "single_repo", "skip"
```

The re-call returns `"started"` (or `"not_a_code_repo"` for `skip`).
Branch as in Phase 2.

### Phase 3 — Status polling during a started scan

After Phase 2 prints the URL and you hand off to the dashboard, the
skill is **hands-off** by design. Per chat turn, you may call
`get_scan_status(scan_id)` **at most once** — and only when the user
asks "how's it going?" / "is it done?" / etc. Never poll in a loop.

Read the status envelope and answer conversationally:

| Field                    | What to do with it                                                   |
|--------------------------|----------------------------------------------------------------------|
| `status`                 | `"completed"` → summarise + offer apply. `"running"` → one-liner.    |
| `progress.completed/total` | "X of Y repos done".                                                |
| `overall_score`          | Render only when `status == "completed"`.                            |
| `prompts_pending_count`  | If > 0, tell the user to answer prompts in the dashboard tab.        |
| `mode_exit_requested`    | If `true`, switch back to chat mode (the user clicked Exit).         |

### Advanced: when NOT to use `scan_and_view`

`scan_and_view` is the right answer for ~99% of skill invocations.
The escape hatches:

- The user explicitly says "don't open the dashboard, just give me
  the JSON" — call `check_workspace_readiness` (workspace) or
  `scan_repo` (single repo) directly. See Phase 4 below.
- You're running headless in CI with no browser — same as above.
- You need to inspect the enumeration envelope before scanning
  (research / debugging) — call `enumerate_workspace` to read the
  full envelope including `classification_hint`, then decide manually.

### Phase 4 — Headless / opt-out path

Used only when the user explicitly opts out of the dashboard.

- **Single repo / monorepo:** `result = scan_repo(path=...)`,
  read `result["overall_score"]` and `result["top_action"]`.
- **Workspace:** `result = check_workspace_readiness(path,
  children_paths=[...])` — synchronous, blocks the chat for ~30s
  per repo. Returns the 5-pillar envelope with per-child cards
  sorted worst-first and a single `top_action` whose `scope` is
  `"workspace"` or `"child"`.

Present: one-line overall + pillar scores, children worst-first
(workspace case), the `top_action` with its `scope`, the verify
command.

### Mid-scan interactive prompts (dashboard mode)

The scanner asks up to six kinds of clarifying question during a scan
(classify / members / umbrella / topaction / ratify / clarify). In
dashboard mode the user answers them inline by clicking buttons in
the PromptsQueue — you do NOT need to relay the question into chat.
If `prompts_pending_count > 0` (from `get_scan_status`) stays > 0
across several turns, gently nudge the user to switch to the browser
tab.

If the user explicitly asks for a question to be answered in chat
("just tell me what it's asking"), read it from
`fetch <snapshot_url>` (or shell out to the dashboard's POST endpoint
to submit on their behalf).

### Exit dashboard mode in chat

When the user asks to exit dashboard mode:

```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"source": "chat"}' \
  <dashboard_url base>/api/scans/<scan_id>/exit
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

- **Never call any tool before `scan_and_view(path)`.** Not
  `enumerate_workspace`, not `scan_repo`, not anything. The front
  door tool replaces all the pre-flight calls. Pre-flighting wastes
  wall-clock chat time (30+ seconds of LLM-thinking between tool
  calls) and lets the LLM get classification wrong on edge cases.
- **Never call `check_workspace_readiness` unless the user explicitly
  opted out of the dashboard** (e.g. "don't open the dashboard / just
  give me the JSON" / headless CI). It is synchronous — for a 17-repo
  workspace that's 5+ minutes of blocked chat. The default for any
  workspace is `scan_and_view` (dashboard mode), which is non-blocking.
- **Never call `check_workspace_readiness` with an empty
  `children_paths`** — the tool will refuse, and rightly so.
- **Never poll `get_scan_status` in a loop.** The dashboard already
  shows live progress over SSE. The skill bridge is hands-off — at
  most one `get_scan_status` call per chat turn, and only when the
  user types in chat.
- **When `status == "needs_disambiguation"`, never read READMEs to
  "double check" before asking.** READMEs do not resolve a
  workspace-vs-monorepo question because every layout has READMEs.
  Paint the pre-rendered prompt and ask the user.
- **Never re-classify in your head.** The scanner already did,
  deterministically, in pure Python. Trust the `status` field.
- **Never auto-run `run_command` actions.** Surface them; let the user
  execute.

## When NOT to use this skill

- The user wants you to write code that uses the agent-readiness
  library (use the docstrings, not this skill).
- The repo is brand-new (< 24h old, 0 commits beyond the initial). The
  Coordination checks won't fire usefully on an empty workspace.

## Worked example A — the clean case (single call)

User says "umbrella" (the 17-repo workspace at
`/Users/me/agent-readiness_project`).

1. **First tool call.** No deliberation, no enumeration, no
   classification. Just:

   ```
   result = scan_and_view(path="/Users/me/agent-readiness_project")
   ```

   Returns in ~2 seconds with:

   ```json
   {
     "status": "started",
     "dashboard_url": "http://127.0.0.1:48217/#/live/<scan_id>",
     "scan_id": "ws-...",
     "children_total": 17,
     "eta_minutes_estimate": 9
   }
   ```

2. **Hand off.** In your next response: print `dashboard_url`
   verbatim, tell the user they can answer prompts in the browser
   and exit dashboard mode anytime (browser button or
   `/agent-readiness exit-dashboard`). Then **stop calling tools**.

3. The dashboard renders the 17-repo grid; per-repo scans run in
   parallel; findings stream over SSE. The user watches progress and
   answers any prompts inline.

4. When the user asks "how's it going?" call
   `get_scan_status(scan_id)` once, summarise conversationally
   ("12 of 17 repos done, overall 78%"), yield. Do not loop.

5. When `status == "completed"`, present the overall score, 5 pillar
   scores, worst children, and the `top_action`. Offer
   `apply_top_action`.

Total elapsed before dashboard URL appears: **~3 seconds**, of which
~2s is the tool call itself. The skill spends zero time thinking
about classification.

## Worked example B — the ambiguous case (single call + one re-call)

User says "scan the umbrella" but they ran `git init` at the root
to track a top-level `AGENTS.md`, so the root *also* has `.git`.

1. **First tool call.** Same as example A:

   ```
   result = scan_and_view(path="/Users/me/agent-readiness_project")
   ```

   This time returns:

   ```json
   {
     "status": "needs_disambiguation",
     "ambiguity_reason": "Root has a .git directory AND one or more children also have .git. This could be (a) a workspace of independent repos that someone put under its own meta-repo, (b) a monorepo where the nested .git dirs are submodules / vendored checkouts, or (c) a single repo whose subdirs happen to be unrelated git checkouts.",
     "ambiguity_options": [
       {"id": "workspace", "label": "Workspace of independent repos", "route": "scan_workspace_async", "hint": "..."},
       {"id": "monorepo", "label": "Monorepo", "route": "scan_repo", "hint": "..."},
       {"id": "single_repo", "label": "Single repo", "route": "scan_repo", "hint": "..."}
     ]
   }
   ```

2. **Paint the prompt verbatim.** No README reads, no improvisation:

   > Root has a .git directory AND one or more children also have
   > .git. This could be (a) a workspace of independent repos
   > someone put under a meta-repo, (b) a monorepo with submodules,
   > or (c) a single repo with unrelated sub-checkouts. Which best
   > describes this path?
   >
   > (a) **Workspace of independent repos** — *(hint quoted from option)*
   > (b) **Monorepo** — *(hint quoted from option)*
   > (c) **Single repo** — *(hint quoted from option)*

3. User picks (a). **Second tool call** with `treat_as`:

   ```
   result = scan_and_view(
       path="/Users/me/agent-readiness_project",
       treat_as="workspace",
   )
   ```

   Returns `status="started"` with the dashboard URL. Continue from
   step 2 of example A.

Total elapsed: ~3s (first call) + user think time + ~3s (re-call) =
the dashboard appears the moment the user picks an option.
