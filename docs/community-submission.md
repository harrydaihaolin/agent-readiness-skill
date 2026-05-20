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
