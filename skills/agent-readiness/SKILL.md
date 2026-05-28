---
name: agent-readiness
description: >-
  Score how agent-ready a code repository or multi-repo workspace is,
  and apply the single highest-priority deterministic fix. Wraps the
  agent-readiness-mcp server (>= 0.8.0). Use when the user asks "is
  this repo agent-ready?", "score this repo / workspace", "what should
  I add to AGENTS.md?", or "fix the top agent-readiness gap". The
  first tool call on any user-supplied path is always
  **`inspect_tool(path)`** — it returns the suggested workspace type
  in ~200ms with zero deliberation on your side. Then call exactly
  ONE of: `scan_repo_tool(path)` (single_repo), `scan_monorepo_tool(path)`
  (monorepo), `scan_workspace_tool(path)` (workspace). Each opens an
  onboarding wizard in the browser at `/#/onboarding/<scan_id>`. The
  user confirms the type and picks which repos to scan before any
  scanning starts — so there's no "wait several minutes only to discover
  we scanned the wrong thing" failure mode. Single repos, monorepos,
  and workspaces all flow through the same dashboard surface; the
  wizard adapts its step strip based on the type. The Coordination
  pillar (workspace-only) measures whether agents can operate
  coherently across a group of repos.
---

# agent-readiness skill

Score how agent-ready a code repository, monorepo, or multi-repo workspace is.

## The contract

**Two tool calls. No more, no less, on a fresh user request.**

1. `inspect_tool(path)` — returns `{enumeration, classification}` in ~200ms.
2. Exactly ONE of `scan_repo_tool` / `scan_monorepo_tool` / `scan_workspace_tool`, picked by `inspect`'s `classification.suggested_type`.

The scan tool opens an onboarding wizard at
`/#/onboarding/<scan_id>`. The wizard's pages let the user **confirm
the type and pick which repos to include before any scanning starts**
— so you can't accidentally spend 5 minutes scanning a 200-package
umbrella when the user wanted just 3 repos. After the user clicks
Start in the browser, the live dashboard takes over with a grid of
per-repo cards animated by a green water-flow progress bar.

**You make ZERO classification decisions.** The classifier is a
deterministic five-branch counting rubric in
``agent-readiness/src/agent_readiness/enumerate_git.py``. If you find
yourself thinking "but maybe this monorepo is actually a workspace
because…" — stop. Trust the classifier and call the corresponding
tool. The user can override in the wizard.

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
    "repos": [ {RepoCandidate}, ... ],
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

| `suggested_type`   | Call                                  | What opens                                              |
|--------------------|---------------------------------------|---------------------------------------------------------|
| `"single_repo"`    | `scan_repo_tool(path)`                | 2-step wizard (Detected → Start), one-card live view.    |
| `"monorepo"`       | `scan_monorepo_tool(path)`            | 3-step wizard with grouped-by-folder picker, grid view.  |
| `"workspace"`      | `scan_workspace_tool(path)`           | 3-step wizard with flat picker grid, grid view.          |

The scan tool returns:

```json
{
  "status": "onboarding_required",
  "scan_id": "demo-b8e52a",
  "dashboard_url": "http://127.0.0.1:57906/#/onboarding/demo-b8e52a",
  "type": "workspace",
  "message": "Onboarding wizard opened. Pick repos and confirm to start scan."
}
```

**Print `dashboard_url` verbatim to the user in your very next response, then stop calling tools.** Example response:

> I opened the onboarding wizard at http://127.0.0.1:57906/#/onboarding/demo-b8e52a.
> Pick which repos you want included and click Start when you're ready.
> The dashboard will then show live progress with per-repo scoring.
>
> To exit dashboard mode without killing the scan: click "Exit dashboard
> mode" in the browser, or type `/agent-readiness exit-dashboard` in chat.

### Phase 3 — Status polling (optional)

Once the user clicks Start in the browser, the scan runs in the
background. **The skill is hands-off by design** — the dashboard owns
the UX. Per chat turn, you may call `get_scan_status_tool(scan_id)`
**at most once**, and only when the user asks "how's it going?" / "is
it done?". Never poll in a loop.

Read the status envelope:

| Field                    | What to do                                                            |
|--------------------------|------------------------------------------------------------------------|
| `status: "completed"`    | Summarise + offer `apply_top_action_tool`.                            |
| `status: "running"`      | One-liner: "X of Y repos done."                                       |
| `progress.completed/total` | "X of Y repos done."                                                 |
| `prompts_pending_count`  | If > 0, tell the user to answer prompts in the dashboard tab.         |
| `mode_exit_requested`    | If `true`, switch back to chat mode (user clicked Exit).              |

## Tool reference

| Tool                          | When                                                              |
|-------------------------------|-------------------------------------------------------------------|
| `inspect_tool`                | Always first. ~200ms. Returns enumeration + classification.       |
| `scan_repo_tool`              | When `suggested_type == "single_repo"`.                           |
| `scan_monorepo_tool`          | When `suggested_type == "monorepo"`.                              |
| `scan_workspace_tool`         | When `suggested_type == "workspace"`.                             |
| `get_scan_status_tool`        | Phase 3 only. ≤1 call per chat turn. Never poll in a loop.        |
| `stop_scan_tool`              | When the user asks to cancel.                                     |
| `apply_top_action_tool`       | After scan completes, when user accepts the fix.                  |
| `list_friction_tool`          | When user wants to see all WARN/ERROR findings.                   |

### Tools you should NOT call from a fresh user request

- `scan_and_view_tool` — **removed in MCP 0.8.0**. Calling it errors.
- `detect_workspace_tool`, `enumerate_workspace_tool` — legacy depth-1
  classifiers from before the typed-tool refactor. The new
  `inspect_tool` supersedes both with smarter git-aware enumeration.
- `check_workspace_readiness_tool` — synchronous blocking workspace
  scan. Avoid for any workspace ≥ 2 repos.

## The Coordination pillar (workspace-only)

Multi-repo workspaces score on four pillars + a fifth: **Coordination**.
Asks whether agents can operate coherently across a group of repos:

- Is there a root `AGENTS.md` declaring member repos and boundaries?
- Are dependency-update orders documented?
- Are coupling pairs annotated (so changing one ratchets the other)?

The Coordination pillar is the single most critical failure mode for
multi-repo agent work per the agentic-engineering literature
(Mabl 2024 "AI agents across services", Bishoy Labib "Coordination
gaps in multi-repo dev environments"). Workspace scans surface
Coordination findings prominently in the dashboard's left column.

## Quick examples

**User: "score ~/code/llm-eval"**

```
inspect_tool(path="/home/user/code/llm-eval")
# → {classification: {suggested_type: "single_repo", confidence: "high"}}

scan_repo_tool(path="/home/user/code/llm-eval")
# → {status: "onboarding_required", dashboard_url: "http://.../#/onboarding/llm-eval-abc123"}
```

Response to user: "I opened the wizard at http://.../#/onboarding/llm-eval-abc123. Confirm and click Start."

**User: "is ~/mle agent-ready?"** (a folder containing 7 nested git projects)

```
inspect_tool(path="/home/user/mle")
# → {classification: {suggested_type: "workspace", confidence: "medium",
#                     rationale: "Root has no .git, 7 nested .git."}}

scan_workspace_tool(path="/home/user/mle")
# → {status: "onboarding_required", dashboard_url: "...", type: "workspace"}
```

Response to user: "I opened the wizard at ... — pick which of the 7 repos you want included."

**User: "score this monorepo"** (root has `.git`, two packages inside)

```
inspect_tool(path=".")
# → {classification: {suggested_type: "monorepo", confidence: "medium"}}

scan_monorepo_tool(path=".")
# → {status: "onboarding_required", dashboard_url: "..."}
```
