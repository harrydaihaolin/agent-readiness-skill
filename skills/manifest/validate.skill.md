---
name: manifest-validate
description: Validate an agent-readiness manifest directory (the bible) for schema correctness, declared-tag consistency, and arch-rule id/filename agreement. Use when authoring or reviewing changes to an agent-readiness-manifest repo, before committing or tagging a release.
---

# manifest-validate

Validate an agent-readiness manifest directory.

## When to use

- Authoring or reviewing changes to a manifest repo (the bible).
- Verifying a workspace's pinned manifest is still well-formed after a
  `git pull` on the manifest.
- Pre-flight before `agent-readiness manifest publish <semver>`
  (manifest publish refuses to tag a release that fails validation).

## What it does

Loads `manifest.yaml`, `glossary.yaml`, `boundaries.yaml`, every
`rules/*.yaml`, and `.agent-readiness-version` from the given
directory. Validates schemas via the protocol package's typed models,
then runs two cross-file semantic checks:

1. boundary rules may only reference tag axes declared in
   `boundaries.spec.tagAxes`;
2. every `rules/<filename>.yaml` must declare `metadata.id` matching
   its numeric filename prefix (e.g. `001-foo.yaml` ⇒ id starts
   `001-`).

## Invocation

Call MCP tool: `mcp__agent_readiness__manifest_validate(path: str = ".")`.

Returns a `ManifestValidationResult` JSON envelope:

```json
{
  "apiVersion": "agent-readiness.io/v1",
  "kind": "ManifestValidationResult",
  "summary": {
    "valid": true,
    "manifest_name": "agent-readiness-reference",
    "errors": 0,
    "warnings": 0,
    "infos": 0
  },
  "issues": []
}
```

When invalid:

```json
{
  "apiVersion": "agent-readiness.io/v1",
  "kind": "ManifestValidationResult",
  "summary": {
    "valid": false,
    "manifest_name": "agent-readiness-reference",
    "errors": 1,
    "warnings": 0,
    "infos": 0
  },
  "issues": [
    {
      "severity": "error",
      "message": "boundary rule 'edge-cannot-import-internal' references undeclared tag axis 'tier' (declared axes: ['scope'])",
      "location": "/path/to/agent-readiness-manifest/boundaries.yaml"
    }
  ]
}
```

## Exit semantics

- `summary.valid == true` → the manifest is safe to consume.
- `summary.valid == false` → fix the listed issues before publishing
  or pinning.
- Issues carry `location` as `path` (or `path:line` for line-precise
  errors). Open the file at that location to address each issue.

## Underlying CLI

`agent-readiness manifest validate <path> [--json]` — exit codes:
0 valid, 1 invalid, 2 internal error.

## Anti-patterns

- Don't run this on a generated workspace's `.workspace/manifest/`
  clone — validate the upstream manifest repo, then
  `agent-readiness update` to roll changes into workspaces.
- Don't bypass validation failures with `--no-validate` (no such flag
  exists); fix the underlying YAML.
