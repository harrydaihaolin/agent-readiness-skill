# agent-readiness-skill rename + multi-harness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rename `agent-readiness-claude-skill` → `agent-readiness-skill`, make the installer multi-target (Claude + Cursor) with auto-detection, and publish the repo as a public GitHub project wired into the main `agent-readiness` install guide.

**Architecture:** Single SKILL.md at repo root (harness-agnostic). Bash installer parses `--target=` flag with default auto-detect against `~/.claude/` and `~/.cursor/`. Docs in `SKILL.md`, `README.md`, and `AGENTS.md` get genericized; the workspace-root `AGENTS.md` repo index gets updated; the main `agent-readiness/README.md` gets a new "Use from your coding agent" section.

**Tech Stack:** Bash, Markdown, YAML frontmatter, GitHub CLI (`gh`).

---

## File Structure

**Renamed (workspace root):**
- `agent-readiness-claude-skill/` → `agent-readiness-skill/`

**Modified (inside renamed `agent-readiness-skill/`):**
- `SKILL.md` — drop `metadata.surfaces` frontmatter; rewrite Installation section.
- `README.md` — title, install steps (Claude + Cursor), curl URL.
- `AGENTS.md` — canonical commands, do-not-touch list.
- `scripts/install.sh` — rewrite for `--target=` flag + auto-detect.

**Modified (elsewhere):**
- `/Users/haolin.dai/Documents/agent-readiness_project/AGENTS.md` — workspace-root repo index (one row).
- `/Users/haolin.dai/Documents/agent-readiness_project/agent-readiness/README.md` — add "Use from your coding agent" section.

**Created (new):**
- `agent-readiness-skill/.git/` (via `git init`).
- GitHub repo: `harrydaihaolin/agent-readiness-skill` (public).

---

## Task 1: Pre-flight + rename the directory

**Files:**
- Modify (rename): `/Users/haolin.dai/Documents/agent-readiness_project/agent-readiness-claude-skill` → `/Users/haolin.dai/Documents/agent-readiness_project/agent-readiness-skill`

- [ ] **Step 1: Verify no existing git state**

Run:
```bash
cd /Users/haolin.dai/Documents/agent-readiness_project && \
  test ! -d agent-readiness-claude-skill/.git && \
  test ! -e agent-readiness-skill && \
  echo OK
```
Expected: `OK`. If `.git` exists or the destination already exists, stop and ask the user — the rename assumptions in the spec don't hold.

- [ ] **Step 2: Verify the gh CLI is authenticated as harrydaihaolin**

Run:
```bash
gh auth status 2>&1 | grep -E "Logged in to github.com|account harrydaihaolin"
```
Expected: a line confirming login. If not authenticated, stop and ask the user to run `gh auth login`.

- [ ] **Step 3: Rename the directory**

Run:
```bash
mv /Users/haolin.dai/Documents/agent-readiness_project/agent-readiness-claude-skill \
   /Users/haolin.dai/Documents/agent-readiness_project/agent-readiness-skill
```
Expected: no output, no error.

- [ ] **Step 4: Verify the rename**

Run:
```bash
ls /Users/haolin.dai/Documents/agent-readiness_project/agent-readiness-skill/SKILL.md && \
  ! ls /Users/haolin.dai/Documents/agent-readiness_project/agent-readiness-claude-skill 2>/dev/null
```
Expected: prints the SKILL.md path, then the second `ls` fails (which is what we want).

- [ ] **Step 5: Commit gate — no commit yet** (repo is not git-initialized; Task 9 does the first commit).

---

## Task 2: Update SKILL.md — drop `metadata.surfaces`, rewrite Installation

**Files:**
- Modify: `agent-readiness-skill/SKILL.md`

- [ ] **Step 1: Remove the `metadata.surfaces` frontmatter block**

Edit `agent-readiness-skill/SKILL.md`. Find:

```
  agent-readiness scanner wheel.
metadata:
  surfaces:
    - claude-code
    - claude-desktop
---
```

Replace with:

```
  agent-readiness scanner wheel.
---
```

- [ ] **Step 2: Rewrite the "## Installation" section**

In the same file, find the section starting `## Installation` (currently around line 106) through end of file. Replace the entire section with:

````markdown
## Installation

The skill works in Claude (Claude Code, Claude Desktop) and Cursor — both
consume the same SKILL.md open-standard format.

### 1. Install the MCP server

```bash
pip install agent-readiness-mcp
```

### 2. Drop SKILL.md into your skills directory

- **Claude**: `~/.claude/skills/agent-readiness/SKILL.md`
- **Cursor (user-level)**: `~/.cursor/skills/agent-readiness/SKILL.md`
- **Cursor (project-level)**: `.cursor/skills/agent-readiness/SKILL.md`

The repo's `scripts/install.sh` does steps 1 and 2 for you and auto-detects
which harnesses you have:

```bash
./scripts/install.sh                  # auto-detect
./scripts/install.sh --target=claude  # force Claude only
./scripts/install.sh --target=cursor  # force Cursor only
./scripts/install.sh --target=both    # both, creating dirs if needed
```

### 3. Wire the MCP server into your harness config

Same JSON payload for both harnesses:

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

Paste into:

- **Claude Desktop / Claude Code**: `~/.claude/claude_desktop_config.json`,
  or run `claude mcp add agent-readiness -- agent-readiness-mcp --transport stdio`.
- **Cursor (user-level)**: `~/.cursor/mcp.json`.
- **Cursor (project-level)**: `.cursor/mcp.json` inside the repo.

Restart the harness to pick up the new server.
````

- [ ] **Step 3: Verify the file**

Run:
```bash
grep -c "surfaces" /Users/haolin.dai/Documents/agent-readiness_project/agent-readiness-skill/SKILL.md
grep -c "Cursor" /Users/haolin.dai/Documents/agent-readiness_project/agent-readiness-skill/SKILL.md
grep -c "~/.cursor/skills/agent-readiness" /Users/haolin.dai/Documents/agent-readiness_project/agent-readiness-skill/SKILL.md
```
Expected: `0`, then a positive integer (≥3), then a positive integer (≥1).

---

## Task 3: Update README.md — title, install steps, curl URL

**Files:**
- Modify: `agent-readiness-skill/README.md`

- [ ] **Step 1: Rewrite the entire README.md**

Overwrite `agent-readiness-skill/README.md` with:

````markdown
# agent-readiness-skill

An [Agent Skill](https://agentskills.io/specification) that wraps the
[`agent-readiness-mcp`](../agent-readiness-mcp) server so coding agents in
**Claude Code, Claude Desktop, and Cursor** can score and fix repositories
with one prompt.

The skill itself is a single `SKILL.md` describing when to use the
underlying tools and how to interpret the result envelope; the actual
work is done by the MCP server.

## Install

The fastest path uses the helper script in this repo. It auto-detects
which of Claude / Cursor you have installed and copies `SKILL.md` into
each, then installs the MCP wheel.

```bash
./scripts/install.sh                  # auto-detect Claude / Cursor
./scripts/install.sh --target=claude  # force Claude only
./scripts/install.sh --target=cursor  # force Cursor only
./scripts/install.sh --target=both    # both, creating dirs if needed
```

It does **not** modify your harness MCP config — that step is intentionally
manual so you know exactly what you're authorising.

### Manual install

1. Install the MCP server:

   ```bash
   pip install agent-readiness-mcp
   ```

2. Drop `SKILL.md` into your skills directory:

   - **Claude**:
     ```bash
     mkdir -p ~/.claude/skills/agent-readiness
     curl -fsSL https://raw.githubusercontent.com/harrydaihaolin/agent-readiness-skill/main/SKILL.md \
       -o ~/.claude/skills/agent-readiness/SKILL.md
     ```
   - **Cursor (user-level)**:
     ```bash
     mkdir -p ~/.cursor/skills/agent-readiness
     curl -fsSL https://raw.githubusercontent.com/harrydaihaolin/agent-readiness-skill/main/SKILL.md \
       -o ~/.cursor/skills/agent-readiness/SKILL.md
     ```

3. Add the MCP server to your harness config:

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

   - **Claude**: paste into `~/.claude/claude_desktop_config.json`, or run
     `claude mcp add agent-readiness -- agent-readiness-mcp --transport stdio`.
   - **Cursor (user-level)**: paste into `~/.cursor/mcp.json`.
   - **Cursor (project-level)**: paste into `.cursor/mcp.json`.

4. Restart the harness. Ask "score this repo for agent readiness" or
   "fix the top agent-readiness gap" to confirm the skill loaded.

## License

MIT.
````

- [ ] **Step 2: Verify the file**

Run:
```bash
grep -c "agent-readiness-claude-skill" /Users/haolin.dai/Documents/agent-readiness_project/agent-readiness-skill/README.md
grep -c "Cursor" /Users/haolin.dai/Documents/agent-readiness_project/agent-readiness-skill/README.md
grep -c "harrydaihaolin/agent-readiness-skill" /Users/haolin.dai/Documents/agent-readiness_project/agent-readiness-skill/README.md
```
Expected: `0`, positive integer (≥3), positive integer (≥2).

---

## Task 4: Rewrite scripts/install.sh — multi-target with auto-detect

**Files:**
- Modify: `agent-readiness-skill/scripts/install.sh`

- [ ] **Step 1: Write a small test harness — define the assertions first**

Create a scratch test runner at `/tmp/test_install.sh` (this file is NOT checked in; it's just for verification before/after the install.sh change):

```bash
cat > /tmp/test_install.sh <<'TESTEOF'
#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="/Users/haolin.dai/Documents/agent-readiness_project/agent-readiness-skill"
SCRIPT="$REPO_DIR/scripts/install.sh"

# Stub out pip so we don't actually install the wheel in tests.
STUB_DIR="$(mktemp -d)"
cat > "$STUB_DIR/python" <<'STUBEOF'
#!/usr/bin/env bash
# Stub: pretend pip install succeeded.
[[ "${1:-}" == "-m" && "${2:-}" == "pip" ]] && exit 0
exec /usr/bin/env python "$@"
STUBEOF
chmod +x "$STUB_DIR/python"

run_case() {
  local name="$1"; shift
  local fake_home="$(mktemp -d)"
  # Pre-create harness dirs based on remaining args until we hit "--".
  while [[ $# -gt 0 && "$1" != "--" ]]; do
    mkdir -p "$fake_home/$1"
    shift
  done
  shift  # consume "--"
  HOME="$fake_home" PATH="$STUB_DIR:$PATH" "$SCRIPT" "$@" > "$fake_home/out" 2>&1 || {
    rc=$?
    echo "[$name] script failed with rc=$rc:"
    cat "$fake_home/out"
    return 1
  }
  echo "[$name] OK"
  for d in .claude/skills/agent-readiness .cursor/skills/agent-readiness; do
    if [[ -f "$fake_home/$d/SKILL.md" ]]; then
      echo "  installed: $d"
    fi
  done
}

# Test 1: auto-detect with only Claude dir present -> installs Claude only.
run_case "auto/claude-only" .claude --

# Test 2: auto-detect with only Cursor dir present -> installs Cursor only.
run_case "auto/cursor-only" .cursor --

# Test 3: auto-detect with both -> installs both.
run_case "auto/both" .claude .cursor --

# Test 4: auto-detect with neither -> error exit.
echo "[auto/neither] expecting error..."
fake_home=$(mktemp -d)
if HOME="$fake_home" PATH="$STUB_DIR:$PATH" "$SCRIPT" > "$fake_home/out" 2>&1; then
  echo "  FAIL: expected non-zero exit when neither dir exists"
  cat "$fake_home/out"
  exit 1
else
  echo "  OK: errored as expected"
fi

# Test 5: --target=both with neither pre-existing -> creates both.
run_case "force/both" -- --target=both

# Test 6: --target=claude with only Cursor present -> still installs Claude only.
run_case "force/claude-only-via-flag" .cursor -- --target=claude

echo
echo "All install.sh test cases passed."
TESTEOF
chmod +x /tmp/test_install.sh
```

- [ ] **Step 2: Run the test against the existing install.sh — expect FAIL**

Run: `/tmp/test_install.sh`

Expected: fails on test 2 (`auto/cursor-only`) or earlier — the current script doesn't know about `--target=` and unconditionally installs to `~/.claude/skills/agent-readiness/`. The failure confirms the test correctly distinguishes old from new behavior.

- [ ] **Step 3: Replace `scripts/install.sh` with the new version**

Overwrite `agent-readiness-skill/scripts/install.sh` with:

```bash
#!/usr/bin/env bash
# Install the agent-readiness skill into Claude and/or Cursor skill dirs,
# alongside the agent-readiness-mcp server.
#
# Default: auto-detect — install to each harness whose home dir exists
# under $HOME. Override with --target=claude|cursor|both|auto.
#
# Does NOT touch any harness MCP config file. Configuring the MCP server
# entry is left to the user so the skill is never the thing that quietly
# rewrites your config.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_SRC="$SCRIPT_DIR/../SKILL.md"

TARGET="auto"
for arg in "$@"; do
  case "$arg" in
    --target=claude|--target=cursor|--target=both|--target=auto)
      TARGET="${arg#--target=}"
      ;;
    -h|--help)
      cat <<USAGE
Usage: $0 [--target=claude|cursor|both|auto]
  auto (default): install to each of Claude/Cursor whose ~ dir exists.
  claude:         install only to ~/.claude/skills/agent-readiness/.
  cursor:         install only to ~/.cursor/skills/agent-readiness/.
  both:           install to both (creating dirs if needed).
USAGE
      exit 0
      ;;
    *)
      echo "error: unknown argument: $arg" >&2
      exit 2
      ;;
  esac
done

if [[ ! -f "$SKILL_SRC" ]]; then
  echo "error: $SKILL_SRC not found; run from inside the skill repo." >&2
  exit 2
fi

install_claude=0
install_cursor=0
case "$TARGET" in
  auto)
    [[ -d "$HOME/.claude" ]] && install_claude=1
    [[ -d "$HOME/.cursor" ]] && install_cursor=1
    if (( install_claude == 0 && install_cursor == 0 )); then
      echo "error: no harness detected — neither ~/.claude/ nor ~/.cursor/ exists." >&2
      echo "       pass --target=claude or --target=cursor explicitly if you want to" >&2
      echo "       install before launching the harness for the first time." >&2
      exit 1
    fi
    ;;
  claude) install_claude=1 ;;
  cursor) install_cursor=1 ;;
  both)   install_claude=1; install_cursor=1 ;;
esac

echo "==> installing agent-readiness-mcp wheel"
python -m pip install --upgrade agent-readiness-mcp

copy_skill() {
  local dest_dir="$1"
  mkdir -p "$dest_dir"
  cp -f "$SKILL_SRC" "$dest_dir/SKILL.md"
  echo "==> copied SKILL.md to $dest_dir"
}

if (( install_claude )); then
  copy_skill "$HOME/.claude/skills/agent-readiness"
fi
if (( install_cursor )); then
  copy_skill "$HOME/.cursor/skills/agent-readiness"
fi

cat <<'NOTE'

Done.

Next step (manual): add the MCP server to your harness config so the skill
can call its tools. Paste this payload:

  {
    "mcpServers": {
      "agent-readiness": {
        "command": "agent-readiness-mcp",
        "args": ["--transport", "stdio"]
      }
    }
  }

…into:
NOTE

if (( install_claude )); then
  echo "  - ~/.claude/claude_desktop_config.json  (Claude Desktop / Claude Code)"
fi
if (( install_cursor )); then
  echo "  - ~/.cursor/mcp.json  (Cursor, user-level)"
  echo "    or .cursor/mcp.json inside a project (Cursor, project-level)"
fi

cat <<'NOTE'

Then restart the harness. Ask "score this repo for agent readiness" to
confirm the skill loaded.
NOTE
```

- [ ] **Step 4: Run shellcheck**

Run: `shellcheck /Users/haolin.dai/Documents/agent-readiness_project/agent-readiness-skill/scripts/install.sh`
Expected: no warnings.

- [ ] **Step 5: Run the test harness again — expect PASS**

Run: `/tmp/test_install.sh`
Expected: `All install.sh test cases passed.`

- [ ] **Step 6: Clean up the test scratch file**

Run: `rm /tmp/test_install.sh`

---

## Task 5: Update repo-local AGENTS.md

**Files:**
- Modify: `agent-readiness-skill/AGENTS.md`

- [ ] **Step 1: Rewrite AGENTS.md**

Overwrite `agent-readiness-skill/AGENTS.md` with:

````markdown
# AGENTS.md

Quick orientation for coding agents working on this repo.

## Canonical commands

```
# install the MCP backend that this skill wraps
pip install -e ../agent-readiness-mcp

# run the install helper (auto-detects Claude / Cursor, copies SKILL.md
# into each that exists). Override with --target=claude|cursor|both.
./scripts/install.sh
./scripts/install.sh --target=both

# lint shell scripts
shellcheck scripts/install.sh
```

## Do not touch

Do not touch these without an explicit ask:

- `SKILL.md`'s frontmatter `name` field — Claude and Cursor both use it as
  the skill id; renaming it breaks every existing install.
- `~/.claude/claude_desktop_config.json` — the install script
  intentionally leaves it alone.
- `~/.cursor/mcp.json` — same: the install script intentionally leaves it
  alone.
- generated install logs.

## Where things live

The skill is the file `SKILL.md` at the repo root. `scripts/install.sh`
is the only helper. Everything else is documentation.

## Reporting issues

Issues with the underlying scoring belong on
[`agent-readiness`](https://github.com/harrydaihaolin/agent-readiness),
not here. Issues with the skill prose or installer belong here.
````

- [ ] **Step 2: Verify the file**

Run:
```bash
grep -c "Cursor" /Users/haolin.dai/Documents/agent-readiness_project/agent-readiness-skill/AGENTS.md
grep -c "~/.cursor/mcp.json" /Users/haolin.dai/Documents/agent-readiness_project/agent-readiness-skill/AGENTS.md
```
Expected: positive integer (≥1) for each.

---

## Task 6: Update workspace-root AGENTS.md repo index row

**Files:**
- Modify: `/Users/haolin.dai/Documents/agent-readiness_project/AGENTS.md` (the row for the renamed repo, around line 54)

- [ ] **Step 1: Update the repo index row**

In `/Users/haolin.dai/Documents/agent-readiness_project/AGENTS.md`, find:

```
| [`agent-readiness-claude-skill`](./agent-readiness-claude-skill) | Claude skill (`SKILL.md`) wrapping the MCP server. | Markdown |
```

Replace with:

```
| [`agent-readiness-skill`](./agent-readiness-skill) | Portable Agent Skill (`SKILL.md`) for Claude and Cursor, wrapping the MCP server. | Markdown |
```

- [ ] **Step 2: Update the explanatory note (line ~21–24) that lists the 5 edge-client repos**

In the same file, find:

```
Note: `PROJECT_MAP.md` lists 12 core repos. The 5 packaging/client repos
below (`mcp`, `claude-skill`, `vscode`, `pre-commit`, `gh-extension`) are
edge surfaces that wrap the core scanner — they post-date the map and
are not yet in the architecture-of-record.
```

Replace with:

```
Note: `PROJECT_MAP.md` lists 12 core repos. The 5 packaging/client repos
below (`mcp`, `skill`, `vscode`, `pre-commit`, `gh-extension`) are
edge surfaces that wrap the core scanner — they post-date the map and
are not yet in the architecture-of-record.
```

- [ ] **Step 3: Verify**

Run:
```bash
grep -c "agent-readiness-claude-skill" /Users/haolin.dai/Documents/agent-readiness_project/AGENTS.md
grep -c "agent-readiness-skill" /Users/haolin.dai/Documents/agent-readiness_project/AGENTS.md
```
Expected: `0` for the first; positive integer (≥1) for the second.

---

## Task 7: Add "Use from your coding agent" section to main `agent-readiness/README.md`

**Files:**
- Modify: `/Users/haolin.dai/Documents/agent-readiness_project/agent-readiness/README.md` (insert between Install (line 33–45) and Design principles (line 47))

- [ ] **Step 1: Insert the new section**

In `agent-readiness/README.md`, find this exact block (lines 41–46):

```
git clone https://github.com/<org>/agent-readiness.git
cd agent-readiness
pip install -e ".[dev]"   # or: make dev
```

## Design principles
```

Replace with:

````markdown
git clone https://github.com/<org>/agent-readiness.git
cd agent-readiness
pip install -e ".[dev]"   # or: make dev
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

## Design principles
````

- [ ] **Step 2: Verify**

Run:
```bash
grep -c "Use from your coding agent" /Users/haolin.dai/Documents/agent-readiness_project/agent-readiness/README.md
grep -c "harrydaihaolin/agent-readiness-skill" /Users/haolin.dai/Documents/agent-readiness_project/agent-readiness/README.md
```
Expected: `1` and a positive integer (≥2).

- [ ] **Step 3: Sanity check that the agent-readiness self-scan still passes**

Run:
```bash
cd /Users/haolin.dai/Documents/agent-readiness_project/agent-readiness && \
  PYTHONPATH=src python3 -m agent_readiness.cli scan . --fail-below 90 2>&1 | tail -20
```
Expected: exit 0 (score ≥ 90; the repo currently dogfoods at 100). If the score drops below 90 because of the README edit, stop and ask the user — the spec assumes the README change is non-regressing.

---

## Task 8: Initial git commit for the renamed skill repo

**Files:**
- Create: `agent-readiness-skill/.git/`

- [ ] **Step 1: Initialize git**

Run:
```bash
cd /Users/haolin.dai/Documents/agent-readiness_project/agent-readiness-skill && \
  git init -b main
```
Expected: `Initialized empty Git repository in .../agent-readiness-skill/.git/`.

- [ ] **Step 2: Stage all current files**

Run:
```bash
cd /Users/haolin.dai/Documents/agent-readiness_project/agent-readiness-skill && \
  git add -- SKILL.md README.md AGENTS.md LICENSE scripts/install.sh \
              docs/superpowers/specs/2026-05-19-agent-readiness-skill-rename-design.md \
              docs/superpowers/plans/2026-05-19-agent-readiness-skill-rename.md \
              .github
```
Expected: no output, no error.

- [ ] **Step 3: Verify the staged set**

Run: `cd /Users/haolin.dai/Documents/agent-readiness_project/agent-readiness-skill && git status --short`
Expected: every staged file shows `A  ...` and no unstaged changes outside the list.

- [ ] **Step 4: Create the initial commit**

Run:
```bash
cd /Users/haolin.dai/Documents/agent-readiness_project/agent-readiness-skill && \
  git commit -m "$(cat <<'EOF'
chore: initial commit — portable agent-readiness skill for Claude + Cursor

Renamed from agent-readiness-claude-skill. SKILL.md is now harness-
agnostic; scripts/install.sh auto-detects Claude / Cursor and supports
--target=claude|cursor|both for explicit control. Design spec and plan
included under docs/superpowers/.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```
Expected: `[main (root-commit) ...] chore: initial commit ...`.

---

## Task 9: Create public GitHub repo and push

**Files:**
- Create: remote `https://github.com/harrydaihaolin/agent-readiness-skill`

- [ ] **Step 1: Confirm intent with the user before any network action**

Before running the next step, the executing agent **must** pause and confirm with the user:
*"I'm about to run `gh repo create harrydaihaolin/agent-readiness-skill --public --source=. --remote=origin --push`. This publishes the repo to GitHub. OK to proceed?"*

Do not proceed without explicit user approval. (This matches the global "ask before publishing" guidance.)

- [ ] **Step 2: Create + push the public repo**

After user approval, run:
```bash
cd /Users/haolin.dai/Documents/agent-readiness_project/agent-readiness-skill && \
  gh repo create harrydaihaolin/agent-readiness-skill \
    --public \
    --description "Agent skill (Claude / Cursor) that scores and fixes agent-readiness in a repo via the agent-readiness-mcp server" \
    --source=. \
    --remote=origin \
    --push
```
Expected: a `https://github.com/harrydaihaolin/agent-readiness-skill` URL printed, and `Pushed commits to ...` confirmation.

- [ ] **Step 3: Verify the repo is public**

Run:
```bash
gh repo view harrydaihaolin/agent-readiness-skill --json visibility,defaultBranchRef
```
Expected: JSON with `"visibility":"PUBLIC"` and `"defaultBranchRef":{"name":"main"}`.

---

## Task 10: Verify the published install URLs work end-to-end

**Files:** none (read-only checks)

- [ ] **Step 1: Confirm the raw SKILL.md URL serves the new content**

Run:
```bash
curl -fsSL https://raw.githubusercontent.com/harrydaihaolin/agent-readiness-skill/main/SKILL.md | head -20
```
Expected: the first 20 lines of the new SKILL.md, including `name: agent-readiness` in frontmatter and **no** `surfaces:` line.

- [ ] **Step 2: Confirm the install.sh dry-run works against the published copy** (optional safety check)

Run:
```bash
fake_home=$(mktemp -d)
mkdir -p "$fake_home/.claude"
HOME="$fake_home" /Users/haolin.dai/Documents/agent-readiness_project/agent-readiness-skill/scripts/install.sh --target=claude 2>&1 | tail -20
ls "$fake_home/.claude/skills/agent-readiness/SKILL.md"
```
Expected: tail prints the "Done" + manual-config message; `ls` prints the SKILL.md path.

- [ ] **Step 3: Spot-check the main repo's README hyperlinks**

Run:
```bash
curl -fsI https://github.com/harrydaihaolin/agent-readiness-skill | head -1
```
Expected: `HTTP/2 200`. If 404, the repo wasn't published or wasn't made public — go back to Task 9.

---

## Self-Review (done after writing this plan)

**1. Spec coverage:**
- Local rename → Task 1. ✓
- `SKILL.md` updates → Task 2. ✓
- `README.md` updates → Task 3. ✓
- `scripts/install.sh` rewrite → Task 4. ✓
- Repo-local `AGENTS.md` → Task 5. ✓
- Workspace-root `AGENTS.md` → Task 6. ✓
- Main `agent-readiness/README.md` → Task 7. ✓
- `git init` + commit → Task 8. ✓
- Publish (public GitHub repo) → Task 9. ✓
- Verification — `shellcheck` (Task 4 step 4), self-scan (Task 7 step 3), curl + visibility (Tasks 9 step 3, 10). ✓
- Auto-memory update — flagged as a follow-up below; not part of the spec scope.

**2. Placeholder scan:** No TBD, no "implement later", no "add appropriate error handling". Every code block is concrete. ✓

**3. Type / name consistency:**
- Repo name: `agent-readiness-skill` everywhere. ✓
- Installer flag: `--target=claude|cursor|both|auto`, identical across SKILL.md (Task 2), README.md (Task 3), install.sh (Task 4), AGENTS.md (Task 5). ✓
- Install dir: `~/.claude/skills/agent-readiness/` and `~/.cursor/skills/agent-readiness/` everywhere. ✓
- GitHub URL: `https://github.com/harrydaihaolin/agent-readiness-skill` everywhere. ✓

## Follow-ups (post-execution, not part of this plan)

- Update auto-memory with a `project` note that the rename + publish shipped on 2026-05-19, so future conversations know the canonical repo name.
- Consider extending the installer to Codex CLI, Gemini CLI, etc. (out of scope per the spec).
