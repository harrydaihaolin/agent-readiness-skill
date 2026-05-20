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
