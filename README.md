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
