# Design: convert `agent-readiness-skill` into a Claude Code plugin

- **Date**: 2026-05-20
- **Author**: Harry Dai (with Claude)
- **Repos touched**: `agent-readiness-skill` (restructured), `agent-readiness` (README pointer)
- **Status**: Approved (brainstorming), ready for implementation plan
- **Related prior spec**: `2026-05-19-agent-readiness-skill-rename-design.md`

## Overview

The current `agent-readiness-skill` repo ships a single `SKILL.md` plus a
shell installer that copies it into `~/.claude/skills/` and/or
`~/.cursor/skills/`. Claude Code's plugin system gives us a better
distribution path: `/plugin install agent-readiness@…` ships the SKILL.md
**and** auto-wires the MCP server, removing the manual
`~/.claude/claude_desktop_config.json` paste that's the biggest install-
time friction today.

This design restructures the repo as a Claude Code plugin **without
dropping Cursor support**: the same repo hosts the plugin layout
(`.claude-plugin/plugin.json`, `skills/agent-readiness/SKILL.md`,
`.mcp.json`) **and** the existing `scripts/install.sh` for harnesses
that don't consume Claude Code plugins (Cursor; Claude Desktop where
plugins aren't wired in).

It also folds in a dogfood-CI fix: the current workflow runs
`agent-readiness scan . --apply-top-action --verify`, which crashes on
this repo because the scanner pins a `modify_manifest_field` action for
`pyproject.toml` and there's no manifest. Restructuring as a plugin
doesn't add a manifest, so we drop `--apply-top-action` from the
dogfood workflow on this repo. The upstream scanner bug (handler
should fall back to `create_file` or skip when the manifest doesn't
exist) is tracked separately.

Community marketplace submission (`/plugin install
agent-readiness@claude-community`) is tracked as a follow-up after this
PR lands; the checklist is included below for reference.

## Background — current state

- Repo: `agent-readiness-skill/`, git-initialized, public on GitHub at
  `harrydaihaolin/agent-readiness-skill`, root commit `393260d`.
- Layout: `SKILL.md` at root, `scripts/install.sh` (auto-detect Claude /
  Cursor with `--target=` flag, python3 fallback), `.github/workflows/{ci,
  dogfood}.yml`, `LICENSE`, `README.md`, `AGENTS.md`, `docs/superpowers/`.
- Install today (Claude path): user pip-installs `agent-readiness-mcp`,
  runs `./scripts/install.sh`, then **manually pastes** the MCP JSON
  payload into `~/.claude/claude_desktop_config.json`.
- Dogfood CI is red: `_apply_modify_manifest_field` raised
  `FileNotFoundError` because the repo has no manifest. Verified via
  the actual GitHub Actions log.

## Goals

- Make Claude Code install zero-config except for the underlying
  `agent-readiness-mcp` pip prerequisite.
- Preserve Cursor + Claude Desktop install via the existing shell
  script and bare SKILL.md (`/.cursor/skills/...`).
- Same repo hosts both the plugin and its marketplace catalog
  (`.claude-plugin/marketplace.json`), so a user can do:
  ```
  /plugin marketplace add harrydaihaolin/agent-readiness-skill
  /plugin install agent-readiness@agent-readiness-skill
  ```
- Unblock dogfood CI on this repo (without modifying the upstream
  scanner).
- Record the community-marketplace submission checklist as repo docs
  so the follow-up step is in shape.

## Non-goals

- Fixing the scanner's `_apply_modify_manifest_field` crash (separate
  PR against `agent-readiness/`). Tracked as the upstream-fix follow-up.
- Changes to `agent-readiness-mcp` itself.
- Changes to the other 4 edge-client repos (`mcp`, `vscode`,
  `pre-commit`, `gh-extension`).
- Performing the community-marketplace submission inside this PR — the
  checklist is documented; the actual submission is parallel work.
- A separate `agent-readiness-marketplace` repo. The marketplace.json
  lives inside `agent-readiness-skill` since there's only one plugin to
  catalog.
- `uvx`/`pipx run` magic to eliminate the pip prerequisite. Considered
  and rejected — adds a `uv`/`pipx` dependency assumption and increases
  fragility. The `pip install agent-readiness-mcp` step remains, but is
  the only manual step.

## Design

### 1. Plugin layout — new files

The repo gains three new content files plus a moved SKILL.md.

#### `.claude-plugin/plugin.json` (new)

```json
{
  "name": "agent-readiness",
  "description": "Score how AI-ready a code repository is and apply the single highest-priority deterministic fix via the agent-readiness-mcp server.",
  "version": "0.1.0",
  "author": { "name": "Harry Dai" },
  "homepage": "https://github.com/harrydaihaolin/agent-readiness",
  "repository": "https://github.com/harrydaihaolin/agent-readiness-skill",
  "license": "MIT"
}
```

Notes:
- `name: "agent-readiness"` matches the SKILL.md `name` field exactly.
  Claude Code namespaces plugin skills/commands as
  `/<plugin-name>:<skill-name>`; since this plugin has one auto-invoked
  skill (not a slash command), the namespacing is mostly internal.
- `version` is set explicitly (`0.1.0`) so consumers only update when
  we bump it. Per the plugin docs, omitting `version` makes every
  commit count as a new version — we want explicit control.

#### `.claude-plugin/marketplace.json` (new)

```json
{
  "name": "agent-readiness-skill",
  "owner": { "name": "Harry Dai" },
  "plugins": [
    {
      "name": "agent-readiness",
      "source": "./",
      "description": "Score how AI-ready a repo is and apply the top fix."
    }
  ]
}
```

Notes:
- `source: "./"` means the plugin lives in the same repo as the
  marketplace.json. Exact key names will be verified against
  `claude plugin validate` during implementation; if the local field
  is `"path"` instead, the implementer adjusts.
- Marketplace `name` matches the repo name for clarity in the
  `@agent-readiness-skill` install suffix.

#### `.mcp.json` (new)

Identical to the JSON payload README currently asks users to paste
into their harness config:

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

When the plugin is enabled, Claude Code auto-loads this MCP server
config — no manual paste required.

#### `skills/agent-readiness/SKILL.md` (moved)

The existing SKILL.md moves from repo root to
`skills/agent-readiness/SKILL.md`. Content stays substantially the
same; the Installation section can be **trimmed** (since the plugin
handles it for Claude users) but should keep a brief reference to the
Cursor manual-install path. The frontmatter `name: agent-readiness`
stays — it matches the plugin name and skill folder name.

### 2. Files that change

#### `scripts/install.sh` (kept, behavior tweaked)

- Source path updates from `$SCRIPT_DIR/../SKILL.md` to
  `$SCRIPT_DIR/../skills/agent-readiness/SKILL.md`.
- Help text mentions that Claude Code users should prefer the plugin
  install (`/plugin install agent-readiness@agent-readiness-skill`).
- Auto-detect behavior unchanged: still installs to `~/.claude/skills/`
  and `~/.cursor/skills/` for whichever exist. The plugin path is
  *additionally* available for Claude Code users via the marketplace.
- Python3 fallback added in the previous spec (line 64) stays.

#### `README.md`

Rewritten to lead with the plugin install path for Claude Code, with
the shell installer as the secondary path for Cursor + Claude Desktop:

- **Section: Install (Claude Code)** — two-line install via
  `/plugin marketplace add … && /plugin install …`.
- **Section: Install (Cursor / Claude Desktop)** — `./scripts/install.sh`
  + the manual `~/.cursor/mcp.json` paste step.
- **Section: Manual install** — same as today's "Manual install".
- **Section: Submission to the community marketplace** — links to the
  new `docs/community-submission.md` checklist file.

#### `AGENTS.md` (repo-local)

- Add the plugin layout to the "Where things live" section.
- Add `claude plugin validate` to canonical commands.
- Update the do-not-touch list with `.claude-plugin/plugin.json` (the
  `name` field is the plugin id; changing it breaks installs).

#### `.github/workflows/dogfood.yml`

Two changes:
1. Drop the `--apply-top-action --verify` flags from the
   `agent-readiness scan` invocation. The scan + score gate stays
   (`--fail-below 90`). This avoids the `modify_manifest_field` crash
   on a repo that legitimately has no language manifest.
2. Add a leading comment explaining the trade-off (no auto-apply on
   this repo because it's docs-only).

#### `.github/workflows/ci.yml`

Add a new job that runs `claude plugin validate ./` (or the
equivalent CLI command for plugin-manifest validation). Job name:
`plugin-validate`. This guards against frontmatter drift between the
plugin manifest, marketplace catalog, and SKILL.md.

If `claude plugin validate` isn't installable in a GitHub Actions
runner without the full Claude Code CLI, the implementer should
substitute a JSON-schema check against the manifests using `jq` or
`python -m json.tool` as a minimum, and add a TODO to revisit when
the CLI is easier to install in CI.

#### `agent-readiness/README.md` (main repo)

Update the "Use from your coding agent" section to lead with the
plugin install command for Claude Code, and keep the manual /
shell-script path for Cursor. Remove the inline JSON paste step from
the Claude Code path.

### 3. Community-marketplace submission checklist

A new file `docs/community-submission.md` is added to the repo with
the following content (paraphrased; final wording is up to the
implementer):

1. Pre-flight: `claude plugin validate ./` returns clean.
2. Repo is public on GitHub — `harrydaihaolin/agent-readiness-skill`.
3. README has install + usage instructions (covered by this PR).
4. SKILL.md `description` is action-triggering — confirm with a
   pre-submission read-through.
5. Plugin `name` (`agent-readiness`) is unique in the community
   catalog — verify against
   `https://github.com/anthropics/claude-plugins-community/blob/main/.claude-plugin/marketplace.json`
   before submitting.
6. `version` field set in `plugin.json` (set to `0.1.0` in this PR).
7. Submit via [claude.ai/settings/plugins/submit](https://claude.ai/settings/plugins/submit)
   or [platform.claude.com/plugins/submit](https://platform.claude.com/plugins/submit).
8. Wait for automated safety screening + human review.
9. Once approved, the community catalog pins a commit SHA. Catalog
   syncs nightly.
10. CI auto-bumps the pin on new commits to `main`.
11. Verify end-to-end:
    ```
    /plugin marketplace add anthropics/claude-plugins-community
    /plugin install agent-readiness@claude-community
    ```

### 4. Cursor + Claude Desktop compatibility

Bare SKILL.md install via `scripts/install.sh` continues to work for:
- Cursor user-level (`~/.cursor/skills/agent-readiness/SKILL.md`)
- Cursor project-level (`.cursor/skills/agent-readiness/SKILL.md`)
- Claude Desktop (drops into `~/.claude/skills/agent-readiness/`)

Plugins are a Claude Code feature, not Claude Desktop. Users on
Claude Desktop without plugin support stay on the shell-installer path.

### 5. Test strategy

- `claude plugin validate ./agent-readiness-skill` runs clean.
- `claude --plugin-dir ./agent-readiness-skill` loads the plugin
  locally; the `agent-readiness` skill is discoverable.
- After `/plugin marketplace add harrydaihaolin/agent-readiness-skill`
  + `/plugin install agent-readiness@agent-readiness-skill`, asking
  Claude "score this repo for agent readiness" against a fixture
  repo triggers the MCP server with no manual config.
- After install, the MCP config is auto-loaded — confirm by checking
  the plugin's runtime state (`/plugin` → Installed tab → plugin
  details lists the MCP server).
- `./scripts/install.sh --target=cursor` against a sandbox `$HOME`
  with `~/.cursor/` present copies the SKILL.md from
  `skills/agent-readiness/SKILL.md` to
  `$HOME/.cursor/skills/agent-readiness/SKILL.md` and prints the
  Cursor MCP config snippet.
- Dogfood CI on the restructured repo no longer crashes; passes the
  `--fail-below 90` gate.
- `shellcheck` clean on the updated `scripts/install.sh`.

## Out of scope (explicit)

- Upstream scanner fix for the `modify_manifest_field` crash on
  manifest-less repos. Belongs in
  `agent-readiness/src/agent_readiness/apply_action.py`; this design
  papers over the symptom by removing `--apply-top-action` from this
  repo's dogfood workflow.
- Performing the community-marketplace submission inside this PR. The
  checklist is captured in `docs/community-submission.md`; the
  submission happens after this lands.
- A separate `agent-readiness-marketplace` repo. Folded into the same
  repo since there's only one plugin.
- Bundling `agent-readiness-mcp` install via `uvx`/`pipx run`. Manual
  `pip install agent-readiness-mcp` stays as the only required step
  outside Claude Code.
- Adding additional skills, agents, hooks, or LSP servers to the
  plugin. Pure 1-skill plugin.

## Open questions

None — all clarifying questions resolved during brainstorming.

## Risks

- **`claude plugin validate` availability in CI**: the CLI may not be
  trivially installable on a GitHub Actions runner. Mitigation: fall
  back to JSON-schema linting + a TODO during implementation.
- **Marketplace.json field names**: the doc preview gave the general
  shape but not the full schema. Mitigation: run `claude plugin
  validate` locally during implementation and adjust before pushing.
- **Plugin namespacing of skills**: the `agent-readiness` skill
  becomes addressable as `/agent-readiness:agent-readiness` if the
  user explicitly slash-invokes it. The skill is *model-invoked* (no
  `disable-model-invocation: true` flag), so this is mostly cosmetic
  — Claude will auto-trigger based on the description regardless.
