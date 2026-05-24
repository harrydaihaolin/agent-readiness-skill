"""Compile neutral-format `<group>/<verb>.skill.md` files into per-host
skill layouts.

For each `skills/<group>/<verb>.skill.md` source, the materialiser
writes both:

    <out_root>/.claude/skills/<group>-<verb>/SKILL.md
    <out_root>/.cursor/skills/<group>-<verb>/SKILL.md

with byte-identical content. The neutral source IS the SKILL.md format
(same frontmatter + body the existing agent-readiness-skill uses), so
materialisation is a pure file copy into each host's expected
directory layout. This keeps both hosts in sync by construction — no
per-host divergence.

Used by:

- ``agent-readiness init-workspace`` — materialises ``manifest/skills/``
  into the generated workspace.
- ``agent-readiness update`` — re-materialises on every update.
- CI in this repo — sanity-check that all ``.skill.md`` compile.

Naming convention::

    skills/<group>/<verb>.skill.md  →  <host>/skills/<group>-<verb>/SKILL.md
"""
from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path


HOST_LAYOUTS: list[tuple[str, str]] = [
    (".claude/skills", "SKILL.md"),
    (".cursor/skills", "SKILL.md"),
]


def _infer_name(src: Path) -> str:
    """``skills/<group>/<verb>.skill.md`` → ``"<group>-<verb>"``."""
    if not src.name.endswith(".skill.md"):
        raise ValueError(f"not a .skill.md file: {src}")
    verb = src.name[: -len(".skill.md")]
    group = src.parent.name
    return f"{group}-{verb}"


def materialize_skill(
    src: Path, *, out_root: Path, name: str | None = None,
) -> None:
    """Materialise one ``.skill.md`` source into both host layouts."""
    src = Path(src)
    out_root = Path(out_root)
    if name is None:
        name = _infer_name(src)
    payload = src.read_bytes()
    for host_dir, filename in HOST_LAYOUTS:
        out = out_root / host_dir / name / filename
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(payload)


def _iter_skill_sources(root: Path) -> Iterable[Path]:
    return sorted(root.rglob("*.skill.md"))


def materialize_directory(src_root: Path, *, out_root: Path) -> int:
    """Materialise every ``.skill.md`` under ``src_root`` into ``out_root``.

    Returns the number of skills written.
    """
    src_root = Path(src_root)
    out_root = Path(out_root)
    n = 0
    for src in _iter_skill_sources(src_root):
        materialize_skill(src, out_root=out_root)
        n += 1
    return n


def main(argv: list[str] | None = None) -> int:
    import argparse

    p = argparse.ArgumentParser(
        prog="materialize",
        description="Compile .skill.md sources into per-host skill layouts.",
    )
    p.add_argument("src", help="Source directory (skills/ root)")
    p.add_argument("--out", default=".", help="Output root (default: cwd)")
    args = p.parse_args(argv)
    n = materialize_directory(Path(args.src), out_root=Path(args.out))
    print(f"materialized {n} skill(s) into {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
