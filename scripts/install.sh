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
PYTHON_BIN=$(command -v python3 || command -v python || true)
if [[ -z "$PYTHON_BIN" ]]; then
  echo "error: neither python3 nor python found in PATH; install Python 3 first." >&2
  exit 2
fi
"$PYTHON_BIN" -m pip install --upgrade agent-readiness-mcp

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
