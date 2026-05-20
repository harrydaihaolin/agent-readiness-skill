# Design: rename `agent-readiness-claude-skill` → `agent-readiness-skill`

- **Date**: 2026-05-19
- **Author**: Harry Dai (with Claude)
- **Repos touched**: `agent-readiness-claude-skill` (renamed), `agent-readiness` (README), workspace-root `AGENTS.md`
- **Status**: Approved (brainstorming), ready for implementation plan

## Overview

The current `agent-readiness-claude-skill` repo ships a single `SKILL.md` that
wraps the `agent-readiness-mcp` server for Claude Code and Claude Desktop.
Cursor now ships Agent Skills using the same `SKILL.md` open standard, so the
existing skill file is already portable — only the harness-specific install
location and MCP config differ.

This design renames the repo to drop the Claude-only framing, makes the
installer multi-target with auto-detection, publishes the repo as a public
GitHub project, and wires it into the main `agent-readiness` install guide.

## Background — current state

- Repo: `agent-readiness-claude-skill/` at the workspace root. Not yet a git
  repo locally; not yet on GitHub.
- Contents: `SKILL.md`, `README.md`, `AGENTS.md`, `LICENSE` (MIT),
  `scripts/install.sh`, `.github/`.
- `SKILL.md` has a non-standard `metadata.surfaces: [claude-code,
  claude-desktop]` frontmatter field and an Installation section that only
  documents the Claude Desktop MCP config.
- `scripts/install.sh` installs `agent-readiness-mcp` via pip, copies
  `SKILL.md` to `~/.claude/skills/agent-readiness/`, and prints the Claude
  MCP config snippet for the user to paste manually. It deliberately does not
  edit any harness config file.
- The workspace-root `AGENTS.md` lists the repo as one of 5 "edge clients +
  packaging" repos that are intentionally not in `agent-readiness-research/PROJECT_MAP.md`
  or `ARCHITECTURE.md`. No update needed in those two files for this rename.

## Goals

- Drop "claude" from the repo identifier — the skill works on Claude and
  Cursor (and any other harness that implements the SKILL.md open standard).
- Installer detects which harness(es) the user has and installs to all
  detected targets by default; supports `--target=claude|cursor|both` for
  explicit control.
- `SKILL.md` and `README.md` document Claude and Cursor side by side.
- Repo is public on GitHub under the user's account
  (`harrydaihaolin/agent-readiness-skill`).
- Main `agent-readiness` repo's `README.md` points users at the new public
  repo with copy-paste install instructions for both harnesses.

## Non-goals

- No changes to `agent-readiness-mcp`, the scoring engine, the SKILL's
  capabilities or workflow text beyond what's needed to genericize away from
  Claude-only language.
- No support for non-Claude/non-Cursor harnesses in this iteration (Codex
  CLI, Gemini CLI, Copilot, etc. will all consume the same SKILL.md but the
  installer won't target them yet).
- No changes to the other 4 edge-client repos (`mcp`, `vscode`, `pre-commit`,
  `gh-extension`).
- No PROJECT_MAP.md / ARCHITECTURE.md updates — the edge-client repos
  remain intentionally out of the architecture-of-record per the workspace
  AGENTS.md.
- The installer continues to deliberately not modify any harness MCP config
  file; that step remains manual and copy-paste.

## Design

### 1. Local rename

`mv agent-readiness-claude-skill agent-readiness-skill` at the workspace
root. The dir is not yet a git repo, so this is a plain filesystem rename
with no GitHub-side redirect needed.

### 2. `SKILL.md` changes

- Remove the `metadata.surfaces: [claude-code, claude-desktop]` block from
  the frontmatter. The Agent Skills open standard doesn't define a `surfaces`
  field, and discovery is handled by each harness's directory scan.
- Rewrite the "Installation" section to cover both harnesses, side-by-side:
  - Claude: `~/.claude/skills/agent-readiness/SKILL.md` + Claude MCP config.
  - Cursor: `~/.cursor/skills/agent-readiness/SKILL.md` + Cursor MCP config
    (`~/.cursor/mcp.json` or project-level `.cursor/mcp.json`).
- Drop the line "Drop this `SKILL.md` into the user's
  `~/.claude/skills/agent-readiness/` directory (or the equivalent in Claude
  Code)." Replace with multi-target text.

The agent-facing workflow (Workflow / Output format / When NOT to use)
sections do not change — they describe the MCP tool contract, which is
harness-agnostic.

### 3. `README.md` changes

- Update the title and opening sentence to reference Claude **and** Cursor.
- Update the `curl` URL from `agent-readiness-claude-skill` to
  `agent-readiness-skill`.
- Add a Cursor block alongside the Claude block in the install steps:
  - Skill directory: `~/.cursor/skills/agent-readiness/`
  - MCP config location: `~/.cursor/mcp.json` (user-level) or
    `.cursor/mcp.json` (project-level)
  - Same MCP config payload (`{"mcpServers": {"agent-readiness": {...}}}`)
- Update the "Helper scripts" section to describe the new auto-detect
  behavior and the `--target=` flag.

### 4. `scripts/install.sh` changes

Behavior:
- Parse `--target=claude|cursor|both` flag. Default: auto-detect.
- Auto-detect: install to Claude if `~/.claude/` exists; install to Cursor
  if `~/.cursor/` exists. If neither exists, print a friendly error and
  exit non-zero.
- `--target=both` installs to both regardless of whether the parent dirs
  exist (creates them if necessary).
- For each chosen target, `mkdir -p` the target skill dir and `cp -f` the
  `SKILL.md`.
- After install, print the MCP config snippet for each chosen target,
  paths included. Continue to deliberately not edit any harness config
  file.
- Keep the `set -euo pipefail` invariant and the idempotency guarantee
  (re-running overwrites the SKILL.md and re-installs the wheel).
- Continue to `pip install --upgrade agent-readiness-mcp` once per run,
  regardless of how many targets.

### 5. `AGENTS.md` (repo-local) changes

- Update canonical commands section to mention the `--target=` flag.
- Update the "Do not touch" list to mention `~/.cursor/mcp.json` alongside
  `~/.claude/claude_desktop_config.json`.
- Update any stale references to "the Claude skill" / "Claude" framing.

### 6. Workspace-root `AGENTS.md` changes

- In the "Edge clients + packaging" table (around line 54), rename the row:
  - `[`agent-readiness-claude-skill`]` → `[`agent-readiness-skill`]`
  - Update the one-liner to mention Cursor as well.

### 7. `agent-readiness/README.md` (main repo) changes

Add a new section titled something like **"Use from your coding agent"**
that:
- Briefly explains that the scanner is available as an Agent Skill for
  Claude Code, Claude Desktop, and Cursor.
- Points at `https://github.com/harrydaihaolin/agent-readiness-skill`.
- Shows the one-liner install (`curl … | bash` against the published
  installer) and the MCP config snippet for each harness.

Section location: near the existing install / usage docs in
`agent-readiness/README.md`. Exact insertion point is a plan-level
detail.

### 8. Publish the repo

In the renamed `agent-readiness-skill/` directory:

1. `git init`, set default branch to `main`.
2. Commit current contents (including this design doc and the file changes
   above) with a single initial commit.
3. `gh repo create harrydaihaolin/agent-readiness-skill --public
   --description "Agent skill (Claude / Cursor) that scores and fixes
   agent-readiness in a repo via the agent-readiness-mcp server" --source=.
   --remote=origin --push`.

The repo's own AGENTS.md already references
`https://github.com/harrydaihaolin/agent-readiness` for upstream issues, so
the user's GitHub identity is confirmed.

## Verification

Before declaring done:

- `shellcheck scripts/install.sh` passes (already canonical in AGENTS.md).
- Dry-run `install.sh` against a sandbox `HOME` for each of: only
  `~/.claude/`, only `~/.cursor/`, both, neither. Confirm correct copies
  and printed config snippets in each case.
- `bash -n scripts/install.sh` (syntax check) — belt and braces.
- `gh repo view harrydaihaolin/agent-readiness-skill --json visibility`
  returns `"PUBLIC"`.
- `curl -fsSL https://raw.githubusercontent.com/harrydaihaolin/agent-readiness-skill/main/SKILL.md`
  returns the new SKILL.md (sanity check that the README's curl URL works).
- Manual smoke: install on a clean Claude Code config, ask "score this repo
  for agent readiness" against a fixture repo, confirm the skill auto-loads
  and the MCP tools respond. Same against Cursor.
- Update auto-memory with a `project` note that this work has shipped, so
  future conversations have the right context.

## Out of scope (explicit)

- Codex CLI, Gemini CLI, GitHub Copilot, OpenCode, Cline, Windsurf install
  steps — they consume the same SKILL.md but the installer won't target
  them in this iteration.
- Restructuring the repo to `skills/agent-readiness/SKILL.md` (proper open-
  standard skill-directory layout). Considered and rejected during
  brainstorming to keep the diff small.
- Adding `scripts/`, `references/`, or `assets/` subdirs to the skill —
  the current SKILL.md is self-contained.
- Changes to `agent-readiness-mcp`, the scanner, the rules pack, or any
  other sibling repo besides the skill repo, the main `agent-readiness`
  repo's README, and the workspace-root AGENTS.md.

## Open questions

None — all clarifying questions resolved during brainstorming.
