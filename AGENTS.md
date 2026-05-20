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
