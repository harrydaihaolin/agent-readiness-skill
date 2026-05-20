# agent-readiness Claude Code Plugin Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restructure `agent-readiness-skill` into a Claude Code plugin with a same-repo marketplace, while keeping `scripts/install.sh` as the Cursor / Claude Desktop fallback. Fix the dogfood CI so the rebuilt repo isn't red on `main`.

**Architecture:** Repo gains `.claude-plugin/{plugin,marketplace}.json`, `.mcp.json`, and moves `SKILL.md` into `skills/agent-readiness/`. The plugin auto-loads the `agent-readiness-mcp` MCP server so Claude Code users skip the manual `~/.claude/claude_desktop_config.json` paste. `scripts/install.sh` keeps working for Cursor/Claude Desktop with an updated source path.

**Tech Stack:** JSON (plugin/marketplace/MCP manifests), Markdown (SKILL.md, docs), bash (install.sh), GitHub Actions YAML.

---

## File Structure

**Created (in `agent-readiness-skill/`):**
- `.claude-plugin/plugin.json` — plugin manifest.
- `.claude-plugin/marketplace.json` — catalog listing this plugin.
- `.mcp.json` — auto-wires the `agent-readiness` MCP server.
- `skills/agent-readiness/SKILL.md` — moved from repo root.
- `docs/community-submission.md` — submission checklist for the community marketplace.

**Modified (in `agent-readiness-skill/`):**
- `scripts/install.sh` — point source path at `../skills/agent-readiness/SKILL.md`; help text mentions plugin install for Claude Code users.
- `README.md` — lead with plugin install (Claude Code); install.sh stays as Cursor / Claude Desktop path.
- `AGENTS.md` — updated layout + canonical commands.
- `.github/workflows/dogfood.yml` — drop `--apply-top-action --verify` (manifest-less repo can't auto-apply manifest fixes).
- `.github/workflows/ci.yml` — add a `plugin-validate` job.

**Deleted (in `agent-readiness-skill/`):**
- `SKILL.md` (root copy — moved to `skills/agent-readiness/SKILL.md`).

**Modified (in main `agent-readiness/`):**
- `README.md` — "Use from your coding agent" section: lead with `/plugin install`, manual JSON paste removed.

---

## Task 1: Pre-flight checks

**Files:** none (read-only).

- [ ] **Step 1: Verify the skill repo is clean and on main**

Run:
```bash
cd /Users/haolin.dai/Documents/agent-readiness_project/agent-readiness-skill && \
  git status --short && \
  git branch --show-current
```
Expected: empty `git status` output (no uncommitted changes from the spec commit step) and `main`.

- [ ] **Step 2: Verify the `claude` CLI is available locally**

Run: `claude --version 2>&1 | head -1`
Expected: a version string. If the command isn't found, stop and ask the user to fix their `claude` install — the plan's validation steps assume it works.

- [ ] **Step 3: Verify `claude plugin validate` exists as a subcommand**

Run: `claude plugin validate --help 2>&1 | head -5`
Expected: usage text. If the subcommand isn't found, note it and substitute `python3 -m json.tool` for JSON syntax checks in later tasks — record this fallback in the implementer's report.

---

## Task 2: Move SKILL.md into the plugin skill directory

**Files:**
- Create: `agent-readiness-skill/skills/agent-readiness/SKILL.md`
- Delete: `agent-readiness-skill/SKILL.md`

- [ ] **Step 1: Create the destination directory**

Run:
```bash
cd /Users/haolin.dai/Documents/agent-readiness_project/agent-readiness-skill && \
  mkdir -p skills/agent-readiness
```
Expected: no output, no error.

- [ ] **Step 2: Move the file with `git mv`**

Run:
```bash
cd /Users/haolin.dai/Documents/agent-readiness_project/agent-readiness-skill && \
  git mv SKILL.md skills/agent-readiness/SKILL.md && \
  git status --short
```
Expected: status shows `R  SKILL.md -> skills/agent-readiness/SKILL.md` (rename detected).

- [ ] **Step 3: Update the moved file's Installation section**

Read `skills/agent-readiness/SKILL.md` and find the entire `## Installation` block at the bottom (everything from `## Installation` through end of file). Replace it with this trimmed block:

````markdown
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
````

This replaces the longer multi-step install block from the previous
revision; users now get most of the install via the plugin and only fall
back to the script for harnesses without plugin support.

- [ ] **Step 4: Verify the moved file**

Run:
```bash
cd /Users/haolin.dai/Documents/agent-readiness_project/agent-readiness-skill && \
  test -f skills/agent-readiness/SKILL.md && \
  test ! -f SKILL.md && \
  grep -c "name: agent-readiness" skills/agent-readiness/SKILL.md && \
  grep -c "plugin marketplace add" skills/agent-readiness/SKILL.md
```
Expected: `1` (frontmatter present), then `1` (new Installation section).

---

## Task 3: Add `.claude-plugin/plugin.json`

**Files:**
- Create: `agent-readiness-skill/.claude-plugin/plugin.json`

- [ ] **Step 1: Create the directory**

Run:
```bash
cd /Users/haolin.dai/Documents/agent-readiness_project/agent-readiness-skill && \
  mkdir -p .claude-plugin
```

- [ ] **Step 2: Write `.claude-plugin/plugin.json`**

Use the Write tool to create `agent-readiness-skill/.claude-plugin/plugin.json` with exactly this content:

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

- [ ] **Step 3: Validate the JSON parses**

Run:
```bash
cd /Users/haolin.dai/Documents/agent-readiness_project/agent-readiness-skill && \
  python3 -m json.tool < .claude-plugin/plugin.json > /dev/null && \
  echo "JSON_OK"
```
Expected: `JSON_OK`.

---

## Task 4: Add `.claude-plugin/marketplace.json`

**Files:**
- Create: `agent-readiness-skill/.claude-plugin/marketplace.json`

- [ ] **Step 1: Write `.claude-plugin/marketplace.json`**

Use the Write tool to create `agent-readiness-skill/.claude-plugin/marketplace.json` with exactly this content:

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

- [ ] **Step 2: Validate the JSON parses**

Run:
```bash
cd /Users/haolin.dai/Documents/agent-readiness_project/agent-readiness-skill && \
  python3 -m json.tool < .claude-plugin/marketplace.json > /dev/null && \
  echo "JSON_OK"
```
Expected: `JSON_OK`.

- [ ] **Step 3: Run `claude plugin validate` if available**

Run:
```bash
cd /Users/haolin.dai/Documents/agent-readiness_project/agent-readiness-skill && \
  claude plugin validate . 2>&1 | tail -20
```
Expected: clean validation output. If validation complains about a missing or wrong `source` key (e.g. expects `"path"` instead of `"source"`, or wants `"./agent-readiness"` instead of `"./"`), update the marketplace.json field according to the validator's message and re-run. Record the corrective change in the implementer's report.

If `claude plugin validate` is not available, skip this step but note it in the report.

---

## Task 5: Add `.mcp.json` (bundled MCP server config)

**Files:**
- Create: `agent-readiness-skill/.mcp.json`

- [ ] **Step 1: Write `.mcp.json`**

Use the Write tool to create `agent-readiness-skill/.mcp.json` with exactly this content:

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

- [ ] **Step 2: Validate the JSON parses**

Run:
```bash
cd /Users/haolin.dai/Documents/agent-readiness_project/agent-readiness-skill && \
  python3 -m json.tool < .mcp.json > /dev/null && \
  echo "JSON_OK"
```
Expected: `JSON_OK`.

---

## Task 6: Local plugin smoke test

**Files:** none (verification only).

- [ ] **Step 1: Validate the full plugin layout**

Run:
```bash
cd /Users/haolin.dai/Documents/agent-readiness_project/agent-readiness-skill && \
  claude plugin validate . 2>&1 | tail -20
```
Expected: clean output, no errors. If a validation issue surfaces, fix the offending file and re-run. If validation is unavailable, skip and rely on Task 14's end-to-end test.

- [ ] **Step 2: Load the plugin with `--plugin-dir`**

This step requires the user (or an interactive session) to run a separate `claude` instance — the implementer should *describe* the command and confirm it's documented, not necessarily execute it in a non-interactive subagent.

Documented verification command (record in the report):
```bash
claude --plugin-dir /Users/haolin.dai/Documents/agent-readiness_project/agent-readiness-skill
```

Once loaded, in that Claude Code session, run `/plugin` and confirm `agent-readiness` appears under Installed (or via `--plugin-dir`). The skill should auto-trigger on a prompt like "score this repo for agent readiness."

If running this interactive step isn't possible during plan execution, mark Task 6 as DONE_WITH_CONCERNS and defer the interactive smoke test to the human partner.

---

## Task 7: Commit the plugin scaffold

**Files:** none new; commits everything from Tasks 2–5.

- [ ] **Step 1: Stage the changes**

Run:
```bash
cd /Users/haolin.dai/Documents/agent-readiness_project/agent-readiness-skill && \
  git add .claude-plugin/ .mcp.json skills/agent-readiness/SKILL.md && \
  git status --short
```
Expected: status shows `A  .claude-plugin/plugin.json`, `A  .claude-plugin/marketplace.json`, `A  .mcp.json`, and `R  SKILL.md -> skills/agent-readiness/SKILL.md`.

- [ ] **Step 2: Commit**

Run:
```bash
cd /Users/haolin.dai/Documents/agent-readiness_project/agent-readiness-skill && \
  git commit -m "$(cat <<'EOF'
feat: add Claude Code plugin layout (plugin.json, marketplace.json, .mcp.json)

Restructure agent-readiness-skill as a Claude Code plugin:
- skills/agent-readiness/SKILL.md replaces the root SKILL.md
- .claude-plugin/plugin.json declares the plugin manifest
- .claude-plugin/marketplace.json publishes this repo as its own marketplace
- .mcp.json auto-wires the agent-readiness MCP server for plugin users

Cursor + Claude Desktop continue to use scripts/install.sh; the SKILL.md
Installation section is trimmed to lead with the plugin install.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)" 2>&1 | tail -5
```
Expected: `[main <sha>] feat: add Claude Code plugin layout ...` with 4 files changed (one rename + three creates).

---

## Task 8: Update `scripts/install.sh` source path

**Files:**
- Modify: `agent-readiness-skill/scripts/install.sh` (line 13)

- [ ] **Step 1: Update the SKILL_SRC path**

Edit the file. Find this exact line (around line 13):

```bash
SKILL_SRC="$SCRIPT_DIR/../SKILL.md"
```

Replace with:

```bash
SKILL_SRC="$SCRIPT_DIR/../skills/agent-readiness/SKILL.md"
```

- [ ] **Step 2: Update the `--help` usage text**

Find this `cat <<USAGE` block:

```bash
      cat <<USAGE
Usage: $0 [--target=claude|cursor|both|auto]
  auto (default): install to each of Claude/Cursor whose ~ dir exists.
  claude:         install only to ~/.claude/skills/agent-readiness/.
  cursor:         install only to ~/.cursor/skills/agent-readiness/.
  both:           install to both (creating dirs if needed).
USAGE
```

Replace with:

```bash
      cat <<USAGE
Usage: $0 [--target=claude|cursor|both|auto]
  auto (default): install to each of Claude/Cursor whose ~ dir exists.
  claude:         install only to ~/.claude/skills/agent-readiness/.
  cursor:         install only to ~/.cursor/skills/agent-readiness/.
  both:           install to both (creating dirs if needed).

  Claude Code users should prefer the plugin install:
    /plugin marketplace add harrydaihaolin/agent-readiness-skill
    /plugin install agent-readiness@agent-readiness-skill
  This script remains the canonical path for Cursor and Claude Desktop.
USAGE
```

- [ ] **Step 3: Run shellcheck**

Run: `shellcheck /Users/haolin.dai/Documents/agent-readiness_project/agent-readiness-skill/scripts/install.sh`
Expected: no warnings.

- [ ] **Step 4: Sandbox dry-run — Cursor target still works**

Run:
```bash
STUB=$(mktemp -d) && \
cat > "$STUB/python3" <<'STUBEOF'
#!/usr/bin/env bash
[[ "${1:-}" == "-m" && "${2:-}" == "pip" ]] && exit 0
exit 1
STUBEOF
chmod +x "$STUB/python3" && \
FAKE_HOME=$(mktemp -d) && \
mkdir -p "$FAKE_HOME/.cursor" && \
HOME="$FAKE_HOME" PATH="$STUB:/usr/bin:/bin" \
  /Users/haolin.dai/Documents/agent-readiness_project/agent-readiness-skill/scripts/install.sh \
  --target=cursor 2>&1 | tail -10 && \
ls "$FAKE_HOME/.cursor/skills/agent-readiness/SKILL.md"
```
Expected: tail prints the "Done. Next step (manual)..." block; `ls` prints the SKILL.md path. The new source path resolved correctly.

---

## Task 9: Update `README.md`

**Files:**
- Modify: `agent-readiness-skill/README.md`

- [ ] **Step 1: Overwrite the README**

Use the Write tool to replace `agent-readiness-skill/README.md` with exactly this content:

````markdown
# agent-readiness-skill

A Claude Code [plugin](https://code.claude.com/docs/en/discover-plugins) and
portable [Agent Skill](https://agentskills.io/specification) that wraps the
[`agent-readiness-mcp`](../agent-readiness-mcp) server so agents in
**Claude Code, Claude Desktop, and Cursor** can score and fix repositories
with one prompt.

The skill itself is a single `SKILL.md` describing when to use the
underlying tools and how to interpret the result envelope; the actual
work is done by the MCP server.

## Install (Claude Code)

The plugin auto-loads the MCP server config so there's no manual JSON
paste:

```
/plugin marketplace add harrydaihaolin/agent-readiness-skill
/plugin install agent-readiness@agent-readiness-skill
```

Prerequisite: `agent-readiness-mcp` must be on your `$PATH`. Install
it once:

```bash
pip install agent-readiness-mcp
```

Then restart Claude Code (or run `/reload-plugins`) and ask
*"score this repo for agent readiness"*.

## Install (Cursor / Claude Desktop)

Plugins are a Claude Code feature; Cursor and Claude Desktop use the
bare SKILL.md format. The repo's `scripts/install.sh` copies it into
each harness's skills directory:

```bash
./scripts/install.sh                  # auto-detect Cursor / Claude Desktop
./scripts/install.sh --target=cursor  # force Cursor only
```

It does **not** modify your harness MCP config. After the script
finishes, paste the MCP JSON it prints into:

- **Cursor (user-level)**: `~/.cursor/mcp.json`
- **Cursor (project-level)**: `.cursor/mcp.json`
- **Claude Desktop**: `~/.claude/claude_desktop_config.json`

Restart the harness to pick up the new server.

## Manual install (any harness)

1. Install the MCP server:
   ```bash
   pip install agent-readiness-mcp
   ```
2. Drop `skills/agent-readiness/SKILL.md` into your skills directory:
   - **Claude**: `~/.claude/skills/agent-readiness/SKILL.md`
   - **Cursor (user-level)**: `~/.cursor/skills/agent-readiness/SKILL.md`
3. Paste the MCP JSON payload (above) into the appropriate config.
4. Restart the harness.

## Community marketplace

This plugin is submitted to the
[community marketplace](https://github.com/anthropics/claude-plugins-community)
as a parallel follow-up. Once approved, install becomes:

```
/plugin marketplace add anthropics/claude-plugins-community
/plugin install agent-readiness@claude-community
```

The submission checklist lives in
[`docs/community-submission.md`](./docs/community-submission.md).

## License

MIT.
````

- [ ] **Step 2: Verify**

Run:
```bash
cd /Users/haolin.dai/Documents/agent-readiness_project/agent-readiness-skill && \
  grep -c "plugin marketplace add harrydaihaolin/agent-readiness-skill" README.md && \
  grep -c "scripts/install.sh" README.md && \
  grep -c "community-submission.md" README.md
```
Expected: each ≥ 1.

---

## Task 10: Update repo-local `AGENTS.md`

**Files:**
- Modify: `agent-readiness-skill/AGENTS.md`

- [ ] **Step 1: Overwrite the file**

Use the Write tool to replace `agent-readiness-skill/AGENTS.md` with:

````markdown
# AGENTS.md

Quick orientation for coding agents working on this repo.

## Canonical commands

```
# install the MCP backend that this skill wraps
pip install -e ../agent-readiness-mcp

# validate the Claude Code plugin layout
claude plugin validate .

# locally load the plugin into Claude Code for testing
claude --plugin-dir .

# run the install helper for Cursor / Claude Desktop (auto-detect dirs).
# Claude Code users should prefer `/plugin install` over this script.
./scripts/install.sh
./scripts/install.sh --target=cursor

# lint shell scripts
shellcheck scripts/install.sh
```

## Do not touch

Do not touch these without an explicit ask:

- `.claude-plugin/plugin.json`'s `name` field — it's the plugin id;
  renaming it breaks every existing install.
- `skills/agent-readiness/SKILL.md`'s frontmatter `name` field —
  Claude and Cursor both use it as the skill id.
- `~/.claude/claude_desktop_config.json` — the install script
  intentionally leaves it alone.
- `~/.cursor/mcp.json` — same: the install script intentionally
  leaves it alone.

## Where things live

- `.claude-plugin/plugin.json` — Claude Code plugin manifest.
- `.claude-plugin/marketplace.json` — same-repo marketplace catalog.
- `.mcp.json` — MCP server config auto-loaded when the plugin is
  enabled in Claude Code.
- `skills/agent-readiness/SKILL.md` — the skill itself.
- `scripts/install.sh` — Cursor / Claude Desktop fallback installer.
- `docs/community-submission.md` — community marketplace submission
  checklist.
- `docs/superpowers/` — design specs + implementation plans.

## Reporting issues

Issues with the underlying scoring belong on
[`agent-readiness`](https://github.com/harrydaihaolin/agent-readiness),
not here. Issues with the plugin manifest, skill prose, or installer
belong here.
````

- [ ] **Step 2: Verify**

Run:
```bash
cd /Users/haolin.dai/Documents/agent-readiness_project/agent-readiness-skill && \
  grep -c "claude plugin validate" AGENTS.md && \
  grep -c "\\.claude-plugin/plugin\\.json" AGENTS.md && \
  grep -c "community-submission.md" AGENTS.md
```
Expected: each ≥ 1.

---

## Task 11: Fix dogfood CI workflow

**Files:**
- Modify: `agent-readiness-skill/.github/workflows/dogfood.yml`

- [ ] **Step 1: Update the workflow**

Edit `agent-readiness-skill/.github/workflows/dogfood.yml`. Find this exact block (lines 39–49 currently):

```yaml
      - name: Self-scan
        # --fail-below 90: gate merges on a minimum readiness score.
        # --apply-top-action: land the single highest-priority structured fix.
        # --verify: run the action's verify command after applying.
        # If verify fails, the workflow exits 1 and the PR is blocked.
        run: |
          agent-readiness scan . \
            --fail-below 90 \
            --apply-top-action \
            --verify \
            --no-progress
```

Replace with:

```yaml
      - name: Self-scan
        # --fail-below 90: gate merges on a minimum readiness score.
        # --apply-top-action is intentionally NOT used here: this repo is
        # docs + a shell installer, with no language manifest, so the
        # scanner's modify_manifest_field handler would crash on apply.
        # Track the upstream fix at:
        #   https://github.com/harrydaihaolin/agent-readiness (apply_action.py).
        run: |
          agent-readiness scan . \
            --fail-below 90 \
            --no-progress
```

- [ ] **Step 2: Verify**

Run:
```bash
cd /Users/haolin.dai/Documents/agent-readiness_project/agent-readiness-skill && \
  grep -c "apply-top-action" .github/workflows/dogfood.yml && \
  grep -c "modify_manifest_field" .github/workflows/dogfood.yml
```
Expected: `0` for the first; `1` for the second.

---

## Task 12: Add `plugin-validate` job to ci.yml

**Files:**
- Modify: `agent-readiness-skill/.github/workflows/ci.yml`

- [ ] **Step 1: Add a new job**

Edit `agent-readiness-skill/.github/workflows/ci.yml`. Append this block at the end of the file (after the `skill-syntax` job):

```yaml

  plugin-validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11 # v4.1.7
      - name: JSON syntax — plugin manifests
        # The `claude` CLI isn't trivially installable on hosted runners
        # right now, so we lint JSON syntax + presence of required keys
        # rather than running `claude plugin validate`. Revisit when the
        # CLI ships an `npx`-style runner.
        run: |
          python3 -m json.tool < .claude-plugin/plugin.json > /dev/null
          python3 -m json.tool < .claude-plugin/marketplace.json > /dev/null
          python3 -m json.tool < .mcp.json > /dev/null
      - name: Required plugin keys
        run: |
          python3 -c "
          import json, sys
          for path, required in [
              ('.claude-plugin/plugin.json', ['name', 'description', 'version']),
              ('.claude-plugin/marketplace.json', ['name', 'plugins']),
              ('.mcp.json', ['mcpServers']),
          ]:
              with open(path) as f:
                  data = json.load(f)
              missing = [k for k in required if k not in data]
              if missing:
                  print(f'{path}: missing keys {missing}')
                  sys.exit(1)
              print(f'{path}: OK')
          "
```

- [ ] **Step 2: Verify the YAML parses**

Run:
```bash
cd /Users/haolin.dai/Documents/agent-readiness_project/agent-readiness-skill && \
  python3 -c "import yaml, sys; yaml.safe_load(open('.github/workflows/ci.yml')); print('YAML_OK')"
```
Expected: `YAML_OK`. (If `python3 -c 'import yaml'` fails because PyYAML isn't installed, fall back to: `python3 -c "import json; print('skipping yaml check, no PyYAML available')"` — the GitHub Actions parser will catch errors on push.)

---

## Task 13: Create `docs/community-submission.md`

**Files:**
- Create: `agent-readiness-skill/docs/community-submission.md`

- [ ] **Step 1: Write the file**

Use the Write tool to create `agent-readiness-skill/docs/community-submission.md` with exactly this content:

````markdown
# Community marketplace submission checklist

Steps to submit `agent-readiness` to the
[community plugin marketplace](https://github.com/anthropics/claude-plugins-community).

## Pre-flight

- [ ] `claude plugin validate .` returns clean against the repo root.
- [ ] Repo is public on GitHub: `harrydaihaolin/agent-readiness-skill`.
- [ ] README has install + usage instructions (covered by this repo).
- [ ] `skills/agent-readiness/SKILL.md`'s `description` is
  action-triggering. Read it as if you've never seen the project —
  would Claude know when to auto-invoke?
- [ ] `name` in `.claude-plugin/plugin.json` (`agent-readiness`) is
  unique in the community catalog. Verify against
  https://github.com/anthropics/claude-plugins-community/blob/main/.claude-plugin/marketplace.json
  before submitting.
- [ ] `version` in `.claude-plugin/plugin.json` is set (currently
  `0.1.0`). Without it, every commit counts as a new version, which
  spams users with update prompts.

## Submit

Choose one:

- **Claude.ai**: https://claude.ai/settings/plugins/submit
- **Console**: https://platform.claude.com/plugins/submit

Both forms collect:
- Public repo URL: `https://github.com/harrydaihaolin/agent-readiness-skill`
- Maintainer contact (your email).

The pipeline runs `claude plugin validate` + automated safety screening
and queues the plugin for human review.

## After approval

- Approved plugins are pinned to a commit SHA in
  `anthropics/claude-plugins-community/.claude-plugin/marketplace.json`.
- The public catalog syncs nightly — there can be a 24h delay between
  approval and your plugin appearing.
- CI auto-bumps the pin on new commits to `main`, so future updates
  ship just by pushing.

## End-to-end install verification

After the catalog sync, confirm:

```
/plugin marketplace add anthropics/claude-plugins-community
/plugin install agent-readiness@claude-community
/reload-plugins
```

Then ask Claude *"score this repo for agent readiness"* against a
fixture repo. It should auto-trigger the skill and invoke the MCP
server with no manual JSON paste.

## Official marketplace

The official marketplace (`claude-plugins-official`) is curated by
Anthropic; inclusion is at their discretion. There is no application
process — promotions happen if/when Anthropic decides. The submission
form goes to the community catalog, not the official one.
````

- [ ] **Step 2: Verify**

Run:
```bash
cd /Users/haolin.dai/Documents/agent-readiness_project/agent-readiness-skill && \
  grep -c "claude plugin validate" docs/community-submission.md && \
  grep -c "harrydaihaolin/agent-readiness-skill" docs/community-submission.md && \
  grep -c "claude-plugins-community" docs/community-submission.md
```
Expected: each ≥ 1.

---

## Task 14: Commit docs + CI updates

**Files:** none new; commits everything from Tasks 8–13.

- [ ] **Step 1: Stage**

Run:
```bash
cd /Users/haolin.dai/Documents/agent-readiness_project/agent-readiness-skill && \
  git add scripts/install.sh README.md AGENTS.md \
          .github/workflows/dogfood.yml .github/workflows/ci.yml \
          docs/community-submission.md && \
  git status --short
```
Expected: every listed file shows `M` or `A`.

- [ ] **Step 2: Commit**

Run:
```bash
cd /Users/haolin.dai/Documents/agent-readiness_project/agent-readiness-skill && \
  git commit -m "$(cat <<'EOF'
docs+ci: update install paths for plugin layout; fix dogfood CI

- install.sh now reads from skills/agent-readiness/SKILL.md and points
  Claude Code users at /plugin install in its help text.
- README leads with the Claude Code plugin install; Cursor / Claude
  Desktop docs stay as a secondary path.
- AGENTS.md describes the new layout.
- ci.yml gains a plugin-validate job that lints the three JSON
  manifests for syntax and required keys.
- dogfood.yml drops --apply-top-action so the manifest-less repo no
  longer crashes the scanner's modify_manifest_field handler. The
  upstream scanner fix is tracked separately.
- docs/community-submission.md captures the steps for the parallel
  follow-up that lands the plugin in @claude-community.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)" 2>&1 | tail -5
```
Expected: `[main <sha>] docs+ci: update install paths ...` with 6 files changed.

---

## Task 15: Update main `agent-readiness/README.md`

**Files:**
- Modify: `/Users/haolin.dai/Documents/agent-readiness_project/agent-readiness/README.md` (the "Use from your coding agent" section)

- [ ] **Step 1: Replace the existing section**

The section was added by the previous spec. Find this exact block:

```
## Use from your coding agent

The scanner is also packaged as an [Agent Skill](https://agentskills.io/specification)
for **Claude Code, Claude Desktop, and Cursor** — ask your agent
*"score this repo for agent readiness"* and it scans + fixes via the
same scoring engine as the CLI.

```bash
# clone the skill repo and run its installer (auto-detects Claude / Cursor)
git clone https://github.com/harrydaihaolin/agent-readiness-skill.git
cd agent-readiness-skill
./scripts/install.sh
```

Then add the MCP server to your harness config (one-time):

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

Paste into `~/.claude/claude_desktop_config.json` (Claude) or
`~/.cursor/mcp.json` (Cursor). See the
[skill repo](https://github.com/harrydaihaolin/agent-readiness-skill) for
manual / per-harness install steps.
```

Replace with:

````markdown
## Use from your coding agent

The scanner is also packaged as a Claude Code
[plugin](https://code.claude.com/docs/en/discover-plugins) and a portable
[Agent Skill](https://agentskills.io/specification). Ask your agent
*"score this repo for agent readiness"* and it scans + fixes via the
same scoring engine as the CLI.

**Claude Code (recommended):** the plugin bundles the MCP server config
— no manual JSON paste.

```
/plugin marketplace add harrydaihaolin/agent-readiness-skill
/plugin install agent-readiness@agent-readiness-skill
```

Prerequisite: `pip install agent-readiness-mcp` once.

**Cursor / Claude Desktop:** clone the skill repo and run its installer
for the bare SKILL.md path, then paste the MCP config it prints into
your harness:

```bash
git clone https://github.com/harrydaihaolin/agent-readiness-skill.git
cd agent-readiness-skill
./scripts/install.sh
```

See the [skill repo](https://github.com/harrydaihaolin/agent-readiness-skill)
for per-harness install details and the community marketplace status.
````

- [ ] **Step 2: Verify**

Run:
```bash
cd /Users/haolin.dai/Documents/agent-readiness_project/agent-readiness && \
  grep -c "/plugin install agent-readiness@agent-readiness-skill" README.md && \
  grep -c "/plugin marketplace add harrydaihaolin/agent-readiness-skill" README.md && \
  grep -c "mcpServers" README.md
```
Expected: each ≥ 1 for the first two; the JSON `mcpServers` line should no longer appear in this section — count should be 0 (the inline JSON paste step was removed; the plugin auto-loads it).

- [ ] **Step 3: Self-scan still passes**

Run:
```bash
cd /Users/haolin.dai/Documents/agent-readiness_project/agent-readiness && \
  PYTHONPATH=src python3 -m agent_readiness.cli scan . --fail-below 90 2>&1 | tail -10
```
Expected: exit 0 (score ≥ 90).

---

## Task 16: Commit + USER GATE before push

**Files:** none new; commits Task 15's changes in the main `agent-readiness` repo.

- [ ] **Step 1: Stage and commit the main repo's README change**

Run:
```bash
cd /Users/haolin.dai/Documents/agent-readiness_project/agent-readiness && \
  git add README.md && \
  git status --short
```
Expected: `M README.md`.

```bash
cd /Users/haolin.dai/Documents/agent-readiness_project/agent-readiness && \
  git commit -m "$(cat <<'EOF'
docs: lead with the Claude Code plugin install in agent-readiness usage

Replace the manual /scripts/install.sh + MCP-JSON-paste flow with the
new /plugin install path. Cursor and Claude Desktop still use the
shell installer for the bare SKILL.md.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)" 2>&1 | tail -3
```
Expected: `[<branch> <sha>] docs: lead with the Claude Code plugin install ...`.

- [ ] **Step 2: PAUSE for user confirmation before pushing either repo**

Push targets:
1. `agent-readiness-skill` → `origin/main` (public; pushes two commits: plugin scaffold + docs/ci).
2. `agent-readiness` → its origin (the main scanner repo).

The implementer **must** stop and confirm with the user:

> "Ready to push. Two repos affected: `agent-readiness-skill` (public, 2 commits) and `agent-readiness` (main repo, 1 commit). OK to push both?"

Do not proceed without explicit user approval.

- [ ] **Step 3: Push both repos after approval**

Run:
```bash
cd /Users/haolin.dai/Documents/agent-readiness_project/agent-readiness-skill && \
  git push origin main 2>&1 | tail -5

cd /Users/haolin.dai/Documents/agent-readiness_project/agent-readiness && \
  git push 2>&1 | tail -5
```
Expected: both `git push` calls complete cleanly. Note any branch / remote issues with the main repo (it may push to a non-`main` branch — confirm with the user before forcing).

---

## Task 17: Verify the published plugin install works end-to-end

**Files:** none (read-only checks against GitHub + a sandbox).

- [ ] **Step 1: Confirm the raw manifest URLs serve the new content**

Run:
```bash
curl -fsSL https://raw.githubusercontent.com/harrydaihaolin/agent-readiness-skill/main/.claude-plugin/plugin.json | python3 -m json.tool | head -5
curl -fsSL https://raw.githubusercontent.com/harrydaihaolin/agent-readiness-skill/main/.claude-plugin/marketplace.json | python3 -m json.tool | head -5
curl -fsSL https://raw.githubusercontent.com/harrydaihaolin/agent-readiness-skill/main/skills/agent-readiness/SKILL.md | head -5
```
Expected: each returns valid output (no 404s); the SKILL.md head shows the frontmatter starting with `---` and `name: agent-readiness`.

- [ ] **Step 2: Confirm the GitHub Actions runs go green**

Run:
```bash
gh run list --repo harrydaihaolin/agent-readiness-skill --limit 5 2>&1 | head -8
```
Expected: the latest two runs (`CI` and `dogfood`) both show `success`. If dogfood is still failing, inspect with `gh run view <id> --repo harrydaihaolin/agent-readiness-skill --log-failed` and report — the plan assumes the apply-top-action removal fixes it.

- [ ] **Step 3: Documented interactive smoke test for the user**

Print this block in the implementer's report so the human partner can run it:

```
# In a fresh Claude Code session:
/plugin marketplace add harrydaihaolin/agent-readiness-skill
/plugin install agent-readiness@agent-readiness-skill
/reload-plugins

# Then prompt:  "score this repo for agent readiness"
# Expect the skill to auto-trigger and call the MCP tools.
```

This step is human-driven (Claude Code is interactive); the implementer just documents and waits for confirmation.

---

## Self-Review (done after writing this plan)

**1. Spec coverage:**

| Spec section | Task |
| --- | --- |
| `.claude-plugin/plugin.json` | Task 3 |
| `.claude-plugin/marketplace.json` | Task 4 |
| `.mcp.json` | Task 5 |
| Move SKILL.md to `skills/agent-readiness/` | Task 2 |
| `scripts/install.sh` source path + help text | Task 8 |
| `README.md` rewrite | Task 9 |
| `AGENTS.md` rewrite | Task 10 |
| `dogfood.yml` (drop `--apply-top-action`) | Task 11 |
| `ci.yml` plugin-validate job | Task 12 |
| `docs/community-submission.md` | Task 13 |
| Main repo `agent-readiness/README.md` | Task 15 |
| Local plugin smoke test | Task 6 |
| End-to-end verification | Task 17 |
| User gate before push | Task 16 step 2 |

All sections of the spec map to one or more tasks. No gaps. ✓

**2. Placeholder scan:** No "TBD", "implement later", or vague "handle edge cases" language. Every step has either complete code, an exact command, or both. ✓

**3. Type/name consistency:**
- Plugin `name` field: `"agent-readiness"` consistent across plugin.json (Task 3), marketplace.json (Task 4), SKILL.md (preserved through move in Task 2), AGENTS.md (Task 10).
- Marketplace name: `"agent-readiness-skill"` consistent in marketplace.json (Task 4), README install line (Task 9), main repo README (Task 15).
- Repo URL: `harrydaihaolin/agent-readiness-skill` consistent everywhere.
- Install command: `/plugin install agent-readiness@agent-readiness-skill` consistent.
- `--target=` flag values (`auto|claude|cursor|both`) unchanged from prior spec.

All consistent. ✓

## Follow-ups (post-execution, not part of this plan)

- Submit to the community marketplace per `docs/community-submission.md`.
- Open an upstream PR against `agent-readiness/` to fix
  `_apply_modify_manifest_field` so it falls back to `create_file` (or
  picks the next action) when the manifest doesn't exist.
- Update the workspace-root `AGENTS.md` repo-index one-liner if the
  plugin restructure warrants a different description (likely yes —
  it's no longer "just a SKILL.md").
- Update auto-memory note with the plugin URL pattern so future
  conversations recommend the right install command.
