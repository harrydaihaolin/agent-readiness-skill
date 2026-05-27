---
name: agent-readiness
description: >-
  Score how agent-ready a code repository or multi-repo workspace is,
  and apply the single highest-priority deterministic fix. Wraps the
  agent-readiness-mcp server. Use when the user asks "is this repo
  agent-ready?", "score this repo / workspace", "what should I add to
  AGENTS.md?", or "fix the top agent-readiness gap". Always call
  `enumerate_workspace` first on the user-supplied path; obey the
  returned `classification_hint.recommended_action` verbatim — do
  not re-classify or deliberate (with agent-readiness 3.4.3+ the
  scanner returns a deterministic classification with `scan_repo` /
  `scan_workspace_async` / `ask_user` / `exit` routing). The skill
  operates in two modes: **chat mode** for single repos / monorepos
  and **dashboard mode** for multi-repo workspaces, where per-repo
  scans stream live to a browser dashboard and interactive prompts
  are answered inline instead of blocking the chat. The Coordination
  pillar (workspace-only) measures whether agents can operate
  coherently across a group of repos.
---

# agent-readiness skill

Score how agent-ready a code repository OR a multi-repo workspace is.
The skill works in three phases:

1. **Enumerate** — call `enumerate_workspace(path)` first. Always.
2. **Classify** — read the enumeration (plus 2–3 READMEs if needed) and
   decide whether `path` is a single repo, a monorepo, a workspace of
   independents, or not a code repo at all.
3. **Scan** — route to one of three tools by classification:
   - single repo / monorepo → `scan_repo(path)` (chat mode, seconds).
   - **workspace (≥ 2 repos) → `scan_workspace_async(path, children_paths)`
     (dashboard mode, returns in ~2s with a `dashboard_url`).** This is
     the default. The chat is NOT blocked.
   - workspace, headless / explicit opt-out only →
     `check_workspace_readiness(path, children_paths)` (synchronous,
     blocks the chat for ~30s per repo). Reserved for CI or when the
     user said "don't open the dashboard".

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
gives you a deterministic classification.

```
result = enumerate_workspace(path="/path/to/dir")
```

The envelope contains `root`, `children[]`, `manifest_signals`,
`stats`, **and `classification_hint`** (added in
agent-readiness 3.4.3 — schema 2).

### Phase 2 — Read `classification_hint` and obey it

The scanner has already classified the path. Read
`result["classification_hint"]["recommended_action"]` and act
verbatim. **Do not re-classify. Do not deliberate. Do not read
READMEs first.** The hint is a pure function of the signals — LLM
judgment cannot improve on it and burns wall-clock chat time.

| `recommended_action`        | What to do                                                                 |
|-----------------------------|----------------------------------------------------------------------------|
| `"scan_repo"`               | Go to Phase 3a (chat-mode single repo / monorepo).                         |
| `"scan_workspace_async"`    | Go to Phase 3b (dashboard mode — default for any multi-repo workspace).    |
| `"ask_user"`                | **STOP. Go to Phase 2.5 below.** Do not scan.                              |
| `"exit"`                    | Tell the user "this is not a code repo", exit.                             |

The hint also carries `classification` (`single_repo` / `monorepo` /
`workspace_of_independents` / `ambiguous` / `not_a_code_repo`),
`confidence` (`high` / `low` / `ambiguous`), and a one-line
`rationale` that names the signals that fired. Quote the rationale
back at the user in your first-turn response — it explains *why* you
chose the scan path you chose.

#### Phase 2.5 — When `recommended_action == "ask_user"`

The signals are ambiguous from data alone (e.g. root has `.git` AND
children also have `.git` — could be a workspace nested in a
meta-repo, a monorepo with submodules, or a single repo with
unrelated sub-checkouts). The scanner already pre-rendered the
disambiguation prompt for you. Paint it into chat verbatim:

```text
{result["classification_hint"]["ambiguity_reason"]}

Which best describes this path?

(a) {ambiguity_options[0]["label"]} — {ambiguity_options[0]["hint"]}
(b) {ambiguity_options[1]["label"]} — {ambiguity_options[1]["hint"]}
(c) {ambiguity_options[2]["label"]} — {ambiguity_options[2]["hint"]}
```

Wait for the user to pick. Then chain the option's `route` field:

- `route == "scan_repo"` → Phase 3a.
- `route == "scan_workspace_async"` → Phase 3b.
- `route == "exit"` → tell the user, stop.

Do NOT improvise alternate wording, do NOT read READMEs to "double
check" — the README will not resolve a workspace-vs-monorepo question
because both layouts have READMEs. The user is the only oracle.

#### Phase 2 — Fallback (for agent-readiness < 3.4.3)

If `classification_hint` is missing from the envelope (you're talking
to an older scanner), fall back to the manual rubric below. For new
installs this branch is dead code.

| Signal                                                                                       | Classification                | Next step                                                                                                                              |
|----------------------------------------------------------------------------------------------|-------------------------------|----------------------------------------------------------------------------------------------------------------------------------------|
| `root.has_git == false` AND ≥ 2 children with `has_git == true`                              | **workspace of independents** | Phase 3b (dashboard mode).                                                                                                              |
| Any `manifest_signals.*` is `true`                                                           | **monorepo**                  | Phase 3a, call `scan_repo(root)`.                                                                                                       |
| `root.has_git == true` AND no children with `.git` AND all signals false                     | **single repo**               | Phase 3a, call `scan_repo(root)`.                                                                                                       |
| Root has neither `.git` nor `README.md` AND enumeration returned zero children               | **not a code repo**           | Tell the user, exit.                                                                                                                    |
| Anything else                                                                                | **ambiguous**                 | Run Phase 2.5 — ask the user, do NOT read READMEs first.                                                                                |

### Phase 3a — Chat mode — single repo / monorepo

```
result = scan_repo(path="/path/to/repo")
print(result["overall_score"])
print(result["top_action"])
```

The `top_action` block contains `action` (a structured edit) and
`verify` (a one-line shell command).

### Phase 3b — Dashboard mode — workspace (DEFAULT)

**This is the path you take for every multi-repo workspace** unless
the user explicitly opted out (see Phase 3c). The MCP tool to call
is `scan_workspace_async` — it returns in ~2 seconds with a
`dashboard_url`. The chat is NOT blocked. Per-repo progress and
interactive prompts stream to the dashboard in the user's browser.

```
session = scan_workspace_async(
    path="/path/to/workspace",
    children_paths=[<paths Claude classified as workspace members>],
)
# session contains: scan_id, dashboard_url, sse_url, snapshot_url
```

Then **tell the user where the dashboard is** in your very next
response and then stop calling tools:

- Print `session["dashboard_url"]` verbatim so they can open it in a
  browser. The URL ends in `/#/live/<scan_id>` — that hash fragment is
  required; the bare base URL loads the legacy workspace browser
  instead of the live page.
- Tell them they can **exit dashboard mode anytime** by typing
  `/agent-readiness exit-dashboard` here in the chat OR by clicking
  the "Exit dashboard mode" button in the browser. Either channel
  returns control to chat mode without killing the scan.
- Hand off — do NOT block the chat tailing the SSE stream and do NOT
  poll `get_scan_status` in a loop. The skill bridge is **hands-off**
  by design (see spec § 4): you only check status when the user types
  in chat.

> Critical: do not call `check_workspace_readiness` in this branch.
> That tool is synchronous and will block the chat for ~30s per child
> — for a 17-repo workspace, that's 5+ minutes of dead chat where the
> user can't see what's happening. The dashboard exists specifically
> to avoid this experience.

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

### Phase 3c — Chat mode — workspace (opt-out only)

Use `check_workspace_readiness` only when **the user explicitly opted
out of dashboard mode** (e.g. "don't open the dashboard, just give me
the JSON" or a headless CI context). Otherwise stay in Phase 3b.

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

- **Never re-classify in your head when `classification_hint` is
  present.** Read `recommended_action` and obey. Deliberating wastes
  wall-clock chat time and the LLM gets ambiguous cases wrong
  (workspaces that happen to also have a meta-`.git` get called
  "monorepo low confidence" and scanned wrong).
- **Never call `scan_repo` on a path you haven't enumerated**, unless
  the user explicitly named the path and it passes a quick `.git/`
  check.
- **Never call `check_workspace_readiness` on a multi-repo workspace
  without explicit opt-out.** It is synchronous — for a 17-repo
  workspace, that is 5+ minutes of blocked chat. The default for any
  workspace is `scan_workspace_async` (dashboard mode). The only
  legitimate uses of `check_workspace_readiness` are: (a) the user
  said "don't open the dashboard / just give me the JSON", (b) you
  are running headless in CI, or (c) the workspace has 1-2 children.
- **Never call `check_workspace_readiness` with an empty
  `children_paths`** — the tool will refuse, and rightly so. Classify
  first.
- **Never poll `get_scan_status` in a loop.** The dashboard already
  shows live progress over SSE. The skill bridge is hands-off — at
  most one `get_scan_status` call per chat turn, and only when the
  user types in chat.
- **When `recommended_action == "ask_user"`, never read READMEs to
  "double check" before asking.** The README will not resolve a
  workspace-vs-monorepo question because both layouts have READMEs.
  Ask the user immediately with the pre-rendered options.
- **Never auto-run `run_command` actions.** Surface them; let the user
  execute.

## When NOT to use this skill

- The user wants you to write code that uses the agent-readiness
  library (use the docstrings, not this skill).
- The repo is brand-new (< 24h old, 0 commits beyond the initial). The
  Coordination checks won't fire usefully on an empty workspace.

## Worked example A — the clean dogfood case

User invokes the skill on `agent-readiness_project/` — a 17-repo
workspace, root has no `.git`.

1. `enumerate_workspace("agent-readiness_project")` returns a
   `classification_hint` block:

   ```json
   {
     "classification": "workspace_of_independents",
     "confidence": "high",
     "recommended_action": "scan_workspace_async",
     "rationale": "root has no .git AND 17 children have .git — classic workspace-of-independents layout"
   }
   ```

2. **Obey the hint.** `recommended_action == "scan_workspace_async"`
   → Phase 3b (dashboard mode). No re-classification, no README
   reads.

   ```
   session = scan_workspace_async(
       path="agent-readiness_project",
       children_paths=[<17 child paths>],
   )
   ```

   Returns in ~2 seconds with `session["dashboard_url"]` (e.g.
   `http://127.0.0.1:48217/#/live/<scan_id>`).

3. In your next response: quote the `rationale` so the user knows
   *why*, print `dashboard_url` verbatim, tell them they can answer
   prompts in the browser and exit dashboard mode anytime (browser
   button or `/agent-readiness exit-dashboard` in chat). Then
   **stop calling tools and yield to the user**.

4. Per-repo scans run in parallel; findings stream to the dashboard
   over SSE. The user watches progress, answers any clarifying
   prompts inline, and asks follow-up questions in chat when ready.

5. When the user asks "how's it going?" or "is it done yet?", call
   `get_scan_status(session["scan_id"])` **once**, summarise the
   envelope conversationally (X of Y repos done, score if completed),
   and yield back. Do not loop.

6. When `status == "completed"`, present the overall score, the 5
   pillar scores, the worst children, and the `top_action`. Offer
   `apply_top_action` if the user wants to land the structured fix.

## Worked example B — the ambiguous case (root + children both have `.git`)

User invokes the skill on `agent-readiness_project/` after they ran
`git init` at the root to track a top-level `AGENTS.md`. Now the root
*also* has `.git`.

1. `enumerate_workspace(...)` returns:

   ```json
   {
     "classification": "ambiguous",
     "confidence": "ambiguous",
     "recommended_action": "ask_user",
     "rationale": "root has .git AND 17 children also have .git",
     "ambiguity_reason": "Root has a .git directory AND one or more children also have .git. This could be (a) a workspace of independent repos that someone put under its own meta-repo, (b) a monorepo where the nested .git dirs are submodules / vendored checkouts, or (c) a single repo whose subdirs happen to be unrelated git checkouts. The signals cannot tell these apart — only you can.",
     "ambiguity_options": [
       {"id": "workspace", "label": "Workspace of independent repos", "route": "scan_workspace_async", "hint": "Each child is its own git repo with its own remote and release cycle. Launch the live dashboard."},
       {"id": "monorepo", "label": "Monorepo", "route": "scan_repo", "hint": "One coherent project; the nested .git directories are submodules / vendored checkouts. Scan the root as one repo."},
       {"id": "single_repo", "label": "Single repo (treat root as one codebase)", "route": "scan_repo", "hint": "The nested .git directories are unrelated; only the root matters for this scan."}
     ]
   }
   ```

2. **Obey the hint — Phase 2.5.** Paint the prompt into chat
   verbatim (do not call any scan tool, do not read READMEs):

   > Root has a .git directory AND one or more children also have
   > .git. This could be (a) a workspace of independent repos that
   > someone put under its own meta-repo, (b) a monorepo where the
   > nested .git dirs are submodules / vendored checkouts, or (c)
   > a single repo whose subdirs happen to be unrelated git
   > checkouts. Which best describes this path?
   >
   > (a) **Workspace of independent repos** — Each child is its own
   >     git repo with its own remote and release cycle. Launch the
   >     live dashboard.
   > (b) **Monorepo** — One coherent project; the nested .git
   >     directories are submodules / vendored checkouts. Scan the
   >     root as one repo.
   > (c) **Single repo (treat root as one codebase)** — The nested
   >     .git directories are unrelated; only the root matters.

3. User picks (a). Chain the option's `route`
   (`scan_workspace_async`) and continue from step 3 of example A.

(For the rare CI / headless case where the user opts out of the
dashboard, Phase 3c uses `check_workspace_readiness` and reports the
same envelope synchronously — at the cost of ~5+ minutes of blocked
chat for this 17-repo workspace.)
