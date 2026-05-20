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
